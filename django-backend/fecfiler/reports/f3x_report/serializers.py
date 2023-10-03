from fecfiler.reports.models import Report
from fecfiler.reports.serializers import ReportSerializerBase
from .models import F3XReport
from django.db import transaction
from django.db.models import Q
from rest_framework.serializers import EmailField, CharField, ValidationError, DateField
from fecfiler.committee_accounts.serializers import CommitteeOwnedSerializer
from fecfiler.web_services.serializers import (
    UploadSubmissionSerializer,
    WebPrintSubmissionSerializer,
)
from fecfiler.validation.serializers import FecSchemaValidatorSerializerMixin
import logging

COVERAGE_DATE_REPORT_CODE_COLLISION = ValidationError(
    {"report_code": ["Collision with existing report_code and year"]}
)

logger = logging.getLogger(__name__)


def get_model_data(data, model):
    return {
        field.name: data[field.name]
        for field in model._meta.get_fields()
        if field.name in data
    }


class F3XReportSerializerBase(ReportSerializerBase):
    schema_name = "F3X"
    confirmation_email_1 = EmailField(
        max_length=44,
        min_length=None,
        allow_blank=True,
        allow_null=True,
        required=False,
    )
    confirmation_email_2 = EmailField(
        max_length=44,
        min_length=None,
        allow_blank=True,
        allow_null=True,
        required=False,
    )
    upload_submission = UploadSubmissionSerializer(
        read_only=True,
    )
    webprint_submission = WebPrintSubmissionSerializer(
        read_only=True,
    )
    report_status = CharField(
        read_only=True,
    )
    report_code_label = CharField(
        read_only=True,
    )

    date_of_election = DateField(required=False, allow_null=True)
    coverage_from_date = DateField(allow_null=True, required=False)
    coverage_through_date = DateField(allow_null=True, required=False)
    date_signed = DateField(allow_null=True, required=False)
    cash_on_hand_date = DateField(allow_null=True, required=False)

    def save(self, **kwargs):
        """Raise a ValidationError if an F3X with the same report code
        exists for the same year
        """
        request = self.context["request"]
        committee_id = request.user.cmtee_id
        number_of_collisions = F3XReport.objects.filter(
            ~Q(id=(self.instance or F3XReport()).id),
            committee_account__committee_id=committee_id,
            coverage_from_date__year=self.validated_data["coverage_from_date"].year,
            report_code=self.validated_data["report_code"],
        ).count()
        if number_of_collisions == 0:
            return super(F3XReportSerializerBase, self).save(**kwargs)
        else:
            raise COVERAGE_DATE_REPORT_CODE_COLLISION

    def create(self, validated_data):
        print("\n\n\n",validated_data,"\n\n")
        with transaction.atomic():
            f3x_data = get_model_data(validated_data, F3XReport)
            f3x_report = F3XReport.objects.create(**f3x_data)
            report_data = validated_data.copy()
            for key in f3x_data.keys():
                print(key)
                if key != "id":
                    del report_data[key]

            if "_form_type" in report_data.keys():
                report_data["form_type"] = report_data.pop("_form_type")

            report = Report.objects.create(**report_data)
            print("\n\n\nCREATED",report,"\n\n")
            report.f3x_report = f3x_report
            report.save()
            return report

    def validate(self, data):
        self.context["fields_to_ignore"] = self.context.get(
            "fields_to_ignore", ["filer_committee_id_number"]
        )
        return super().validate(data)

    class Meta:
        model = F3XReport
        fields = [
            f.name
            for f in F3XReport._meta.get_fields()
            if f.name
            not in [
                "deleted",
                "schatransaction",
                "scheduleatransaction",
                "schedulebtransaction",
                "transaction",
                "report",
                "dotfec",
                "memotext",
                "uploadsubmission",
                "webprintsubmission",
            ]
        ] + ["report_status", "report_code_label", "fields_to_validate"]
        read_only_fields = ["id", "deleted", "created", "updated"]
