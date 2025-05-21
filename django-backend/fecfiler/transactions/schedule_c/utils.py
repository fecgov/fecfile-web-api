from fecfiler.transactions.models import Transaction
from fecfiler.transactions.schedule_c2.utils import carry_forward_guarantor
from django.forms.models import model_to_dict
from fecfiler.utils import save_copy
from django.db.models import Q
from decimal import Decimal
from ..utils import add_org_ind_contact, add_candidate_contact
from silk.profiling.profiler import silk_profile


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


@silk_profile(name="carry_forward_loans")
def carry_forward_loans(report):
    if report.previous_report:
        loans_to_carry_forward = Transaction.objects.transaction_view().filter(
            ~Q(loan_balance=Decimal(0)) | Q(loan_balance__isnull=True),
            ~Q(memo_code=True),
            reports=report.previous_report,
            schedule_c_id__isnull=False,
            committee_account__id=report.committee_account.id,
        )

        for loan in loans_to_carry_forward:
            carry_forward_loan(loan, report)


@silk_profile(name="carry_forward_loan")
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
