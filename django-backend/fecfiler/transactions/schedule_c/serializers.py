import logging

from django.db import transaction, models
from django.db.models import Q
from fecfiler.transactions.schedule_c.models import ScheduleC
from fecfiler.transactions.models import Transaction
from fecfiler.reports.models import Report
from fecfiler.transactions.serializers import TransactionSerializerBase
from fecfiler.shared.utilities import get_model_data
from rest_framework.fields import DecimalField, CharField, DateField, BooleanField
import copy

logger = logging.getLogger(__name__)


class ScheduleCTransactionSerializer(TransactionSerializerBase):
    def to_internal_value(self, data):
        internal = super().to_internal_value(data)
        transaction = TransactionSerializerBase(context=self.context).to_internal_value(
            data
        )
        internal.update(transaction)
        return internal

    def validate(self, data):
        """Adds stub aggregate_amount to pass validation"""
        validated_data = super().validate(data)
        return validated_data

    def create(self, validated_data: dict):
        with transaction.atomic():
            schedule_c_data = get_model_data(validated_data, ScheduleC)
            schedule_c = ScheduleC.objects.create(**schedule_c_data)
            transaction_data = validated_data.copy()
            transaction_data["schedule_c_id"] = schedule_c.id
            for key in schedule_c_data.keys():
                if key != "id":
                    del transaction_data[key]

            schedule_c_transaction = super().create(transaction_data)
            if not schedule_c_transaction.memo_code:
                self.create_in_future_reports(schedule_c_transaction)
            return schedule_c_transaction

    def update(self, instance, validated_data: dict):
        with transaction.atomic():
            for attr, value in validated_data.items():
                if attr != "id":
                    setattr(instance.schedule_c, attr, value)
            instance.schedule_c.save()
            schedule_c_transaction = super().update(instance, validated_data)
            if not schedule_c_transaction.memo_code:
                self.update_in_future_reports(schedule_c_transaction, validated_data)
            return schedule_c_transaction

    def get_future_in_progress_reports(self, report: Report):
        print(str(report.__dict__))
        return Report.objects.get_queryset().filter(
            ~Q(id=report.id),
            committee_account=report.committee_account_id,
            upload_submission__isnull=True,
            coverage_through_date__gte=report.coverage_through_date,
        )

    def create_in_future_reports(self, transaction: Transaction):
        report = transaction.report
        future_reports = self.get_future_in_progress_reports(report)
        schedule_c_copies_to_insert = []
        transaction_copies_to_insert = []
        for report in future_reports:
            schedule_c_copy = copy.deepcopy(transaction.schedule_c)
            schedule_c_copy.id = None
            schedule_c_copies_to_insert.append(schedule_c_copy)
            transaction_copy = copy.deepcopy(transaction)
            transaction_copy.id = None
            transaction_copy.report = report
            transaction_copy.schedule_c = schedule_c_copy
            transaction_copies_to_insert.append(transaction_copy)
        ScheduleC.objects.bulk_create(schedule_c_copies_to_insert)
        Transaction.objects.bulk_create(transaction_copies_to_insert)

    def update_in_future_reports(self, transaction: Transaction, validated_data: dict):
        report = transaction.report
        future_reports = self.get_future_in_progress_reports(report)
        transactions_to_update = Transaction.objects.filter(
            transaction_id=transaction.transaction_id,
            report_id__in=models.Subquery(
                future_reports.values('id')
            )
        )
        schedule_cs_to_update = ScheduleC.objects.filter(
            transaction__schedule_c_id__in=models.Subquery(
                transactions_to_update.values('schedule_c_id')
            )
        )
        schedule_c_data = get_model_data(validated_data, ScheduleC)
        del schedule_c_data['id']
        schedule_cs_to_update.update(**schedule_c_data)
        transaction_data = get_model_data(validated_data, Transaction)
        del transaction_data['id']
        transactions_to_update.update(**transaction_data)

    receipt_line_number = CharField(required=False, allow_null=True)
    lender_organization_name = CharField(required=False, allow_null=True)
    lender_last_name = CharField(required=False, allow_null=True)
    lender_first_name = CharField(required=False, allow_null=True)
    lender_middle_name = CharField(required=False, allow_null=True)
    lender_prefix = CharField(required=False, allow_null=True)
    lender_suffix = CharField(required=False, allow_null=True)
    lender_street_1 = CharField(required=False, allow_null=True)
    lender_street_2 = CharField(required=False, allow_null=True)
    lender_city = CharField(required=False, allow_null=True)
    lender_state = CharField(required=False, allow_null=True)
    lender_zip = CharField(required=False, allow_null=True)
    election_code = CharField(required=False, allow_null=True)
    election_other_description = CharField(required=False, allow_null=True)
    loan_amount = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    loan_payment_to_date = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    loan_balance = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    loan_incurred_date = DateField(required=False, allow_null=True)
    loan_due_date = CharField(required=False, allow_null=True)
    loan_interest_rate = CharField(required=False, allow_null=True)
    secured = BooleanField(required=False, allow_null=True, default=False)
    personal_funds = BooleanField(required=False, allow_null=True, default=False)
    lender_committee_id_number = CharField(required=False, allow_null=True)
    lender_candidate_id_number = CharField(required=False, allow_null=True)
    lender_candidate_last_name = CharField(required=False, allow_null=True)
    lender_candidate_first_name = CharField(required=False, allow_null=True)
    lender_candidate_middle_name = CharField(required=False, allow_null=True)
    lender_candidate_prefix = CharField(required=False, allow_null=True)
    lender_candidate_suffix = CharField(required=False, allow_null=True)
    lender_candidate_office = CharField(required=False, allow_null=True)
    lender_candidate_state = CharField(required=False, allow_null=True)
    lender_candidate_district = CharField(required=False, allow_null=True)
    memo_text_description = CharField(required=False, allow_null=True)

    class Meta(TransactionSerializerBase.Meta):
        fields = (
            TransactionSerializerBase.Meta.get_fields()
            + [
                f.name
                for f in ScheduleC._meta.get_fields()
                if f.name not in ["transaction"]
            ]
            + ["loan_balance", "loan_payment_to_date"]
        )
