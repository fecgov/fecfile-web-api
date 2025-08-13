from fecfiler.transactions.models import Transaction
from fecfiler.transactions.schedule_c.models import ScheduleC
from fecfiler.transactions.schedule_c2.models import ScheduleC2
from fecfiler.memo_text.models import MemoText
from fecfiler.transactions.schedule_c2.utils import carry_forward_guarantor
from django.forms.models import model_to_dict
from fecfiler.utils import save_copy
from django.db.models import Q
from django.db import transaction
from decimal import Decimal
from ..utils import add_org_ind_contact, add_candidate_contact
import uuid
from fecfiler.reports.models import ReportTransaction


def add_schedule_c_contact_fields(instance, representation=None):
    data = {}
    if instance.contact_1:
        add_org_ind_contact(data, instance.contact_1, "lender")
        data["lender_committee_id_number"] = instance.contact_1.committee_id
    if instance.contact_2:
        add_candidate_contact(data, instance.contact_2, "lender", False)

    if representation:
        representation.update(data)
    else:
        for k, v in data.items():
            setattr(instance, k, v)


def carry_forward_loans(report):
    if report.previous_report:
        with transaction.atomic():
            loans_to_carry_forward = Transaction.objects.transaction_view().filter(
                ~Q(loan_balance=Decimal(0)) | Q(loan_balance__isnull=True),
                ~Q(memo_code=True),
                reports=report.previous_report,
                schedule_c_id__isnull=False,
                committee_account__id=report.committee_account.id,
            )
            loan_models_dict = {}

            create_carry_forward_loan_schedule_c_list(
                loans_to_carry_forward, loan_models_dict, report
            )
            create_carry_forward_loan_memo_text_list(
                loans_to_carry_forward, loan_models_dict
            )
            carry_forward_loan_transaction_list = (
                create_carry_forward_loan_transaction_list(
                    loans_to_carry_forward, loan_models_dict, report
                )
            )
            create_report_transaction_list(carry_forward_loan_transaction_list)


def create_carry_forward_loan_schedule_c_list(
    loans_to_carry_forward, loan_models_dict, report
):
    schedule_c_list = []
    for loan in loans_to_carry_forward:
        schedule_c_copy = copy_schedule_c_for_loan(loan, report)
        schedule_c_list.append(schedule_c_copy)
        loan_models_dict[loan.id]["schedule_c_id"] = (
            schedule_c_copy.pk if schedule_c_copy else None
        )
    return ScheduleC.objects.bulk_create(schedule_c_list)


def create_carry_forward_loan_memo_text_list(loans_to_carry_forward, loan_models_dict):
    memo_text_list = []
    for loan in loans_to_carry_forward:
        memo_text_copy = copy_memo_text_for_loan(loan)
        memo_text_list.append(memo_text_copy)
        loan_models_dict[loan.id]["memo_text_id"] = (
            memo_text_copy.pk if memo_text_copy else None
        )
    return MemoText.objects.bulk_create(memo_text_list)


def create_carry_forward_loan_transaction_list(
    loans_to_carry_forward, loan_models_dict, report
):
    transaction_list = []
    child_schedule_c2_list = []
    child_transaction_list = []
    for loan in loans_to_carry_forward:
        schedule_c_id = loan_models_dict[loan.id]["schedule_c_id"]
        memo_text_id = loan_models_dict[loan.id]["memo_text_id"]
        transaction_copy = copy_transaction_for_loan(
            loan, schedule_c_id, memo_text_id, report
        )
        transaction_list.append(transaction_copy)
        loan_models_dict[loan.id]["transaction_id"] = transaction_copy.pk
        for child in list(loan.children):
            if child.schedule_c2 is not None:
                schedule_c2_copy = copy_schedule_c2_for_loan_child(child)
                child_schedule_c2_list.append(schedule_c2_copy)
                child_transaction_copy = copy_transaction_for_loan_child(
                    child, transaction_copy, schedule_c2_copy.pk, report
                )
                child_transaction_list.append(child_transaction_copy)

    ScheduleC2.objects.bulk_create(child_schedule_c2_list)
    return Transaction.objects.bulk_create(transaction_list + child_transaction_list)


def create_report_transaction_list(transaction_list, report):
    report_transaction_list = []
    for txn in transaction_list:
        report_transaction_list.append(
            ReportTransaction(
                **{
                    "report_id": report.id,
                    "transaction_id": txn.id,
                }
            )
        )
    return ReportTransaction.objects.bulk_create(report_transaction_list)


def copy_schedule_c_for_loan(loan, report):
    if loan.schedule_c:
        schedule_c_copy = ScheduleC(
            **model_to_dict(
                loan.schedule_c,
                fields=[f.name for f in ScheduleC._meta.fields],
                exclude=[
                    "report_coverage_through_date",
                ],
            )
        )
        schedule_c_copy.pk = uuid.uuid4()
        schedule_c_copy.report_coverage_through_date = report.coverage_through_date
        return schedule_c_copy
    return None


def copy_memo_text_for_loan(loan):
    if loan.memo_text:
        memo_text_copy = MemoText(
            **model_to_dict(
                loan.memo_text,
                fields=[f.name for f in MemoText._meta.fields],
            )
        )
        memo_text_copy.pk = uuid.uuid4()
        return memo_text_copy
    return None


def copy_transaction_for_loan(loan, schedule_c_id, memo_text_id, report):
    transaction_copy = Transaction(
        **model_to_dict(
            loan,
            fields=[f.name for f in Transaction._meta.fields],
            exclude=[
                "committee_account",
                "report",
                "contact_1",
                "contact_2",
                "contact_3",
                "schedule_c",
                "loan",
                "memo_text",
            ],
        )
    )
    transaction_copy.pk = uuid.uuid4()
    transaction_copy.schedule_c_id = schedule_c_id
    transaction_copy.memo_text_id = memo_text_id
    transaction_copy.contact_1_id = loan.contact_1_id
    transaction_copy.contact_2_id = loan.contact_2_id
    transaction_copy.contact_3_id = loan.contact_3_id
    transaction_copy.committee_account_id = loan.committee_account_id
    # The loan_id should point to the original loan transaction
    # even if the loan is pulled forward multiple times.
    transaction_copy.loan_id = (loan.loan_id or loan.id,)
    transaction_copy.report_id = report.id
    return transaction_copy


def copy_schedule_c2_for_loan_child(loan_child):
    if loan_child.schedule_c2:
        schedule_c2_copy = ScheduleC2(
            **model_to_dict(
                loan_child.schedule_c2,
                fields=[f.name for f in ScheduleC2._meta.fields],
            )
        )
        schedule_c2_copy.pk = uuid.uuid4()
        return schedule_c2_copy
    return None


def copy_transaction_for_loan_child(
    loan_child, new_loan_parent_transaction, new_loan_child_schedule_c2_id, report
):
    transaction_copy = Transaction(
        **model_to_dict(
            loan_child,
            fields=[f.name for f in Transaction._meta.fields],
            exclude=[
                "committee_account",
                "report",
                "parent_transaction",
                "contact_1",
                "contact_2",
                "contact_3",
                "schedule_c2",
            ],
        )
    )
    transaction_copy.contact_1_id = loan_child.contact_1_id
    transaction_copy.contact_2_id = loan_child.contact_2_id
    transaction_copy.contact_3_id = loan_child.contact_3_id
    transaction_copy.schedule_c2_id = new_loan_child_schedule_c2_id
    transaction_copy.committee_account_id = (
        new_loan_parent_transaction.committee_account_id
    )
    transaction_copy.report_id = report.id
    transaction_copy.parent_transaction_id = new_loan_parent_transaction.id
    return transaction_copy


def carry_forward_loan(loan, report):
    # force evaluation of lazy query. if not, the loan.children
    # will be a different queryset after the copy is saved
    original_children = list(loan.children)
    loan_data = {
        "schedule_c": save_copy(
            loan.schedule_c,
            {"report_coverage_through_date": report.coverage_through_date},
        ),
        "memo_text": save_copy(loan.memo_text) if loan.memo_text else None,
        "contact_1_id": loan.contact_1_id,
        "contact_2_id": loan.contact_2_id,
        "contact_3_id": loan.contact_3_id,
        "committee_account_id": loan.committee_account_id,
        # The loan_id should point to the original loan transaction
        # even if the loan is pulled forward multiple times.
        "loan_id": loan.loan_id or loan.id,
    }
    new_loan = save_copy(
        Transaction(
            **model_to_dict(
                loan,
                fields=[f.name for f in Transaction._meta.fields],
                exclude=[
                    "committee_account",
                    "report",
                    "contact_1",
                    "contact_2",
                    "contact_3",
                    "schedule_c",
                    "loan",
                    "memo_text",
                ],
            )
        ),
        loan_data,
        links={"reports": [report]},
    )

    for child in original_children:
        # If child is a guarantor transaction, copy it
        # and link it to the new loan
        if child.schedule_c2 is not None:
            carry_forward_guarantor(report, new_loan, child)
