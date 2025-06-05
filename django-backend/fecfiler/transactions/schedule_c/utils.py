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

        loans_dict = {
            loan.id: {
                "schedule_c_id": copy_schedule_c(loan, report),
                "memo_id": copy_memo_text(loan),
            }
            for loan in loans_to_carry_forward
        }
        print(f"Carrying forward {loans_dict} loans to report {report.id}")
        for loan in loans_to_carry_forward:
            carry_forward_loan_2(
                loan,
                report,
                loans_dict[loan.id]["schedule_c_id"],
                loans_dict[loan.id]["memo_id"],
            )


def copy_schedule_c(loan, report):
    """
    Copies the schedule_c of the loan to a new schedule_c
    returns ID of the new schedule_c if it exists, otherwise None.
    """
    schedule_c = save_copy(
        loan.schedule_c,
        {"report_coverage_through_date": report.coverage_through_date},
    )
    return schedule_c.id if schedule_c else None


def copy_memo_text(loan):
    """
    Copies the memo_text of the loan to a new memo_text.
    Returns ID of the new memo_text if it exists, otherwise None.
    """
    memo = save_copy(loan.memo_text) if loan.memo_text else None

    return memo.id if memo else None


def carry_forward_loan_2(loan, report, schedule_c_id, memo_id=None):
    """
    Carry forward a loan transaction to a new report.
    """
    loan_data = {
        "transaction_type_identifier": loan.transaction_type_identifier,
        "aggregation_group": loan.aggregation_group,
        "parent_transaction_id": loan.parent_transaction_id,
        "_form_type": loan._form_type,
        "transaction_id": loan.transaction_id,
        "entity_type": loan.entity_type,
        "memo_code": loan.memo_code,
        "itemized": loan.itemized,
        "force_itemized": loan.force_itemized,
        "force_unaggregated": loan.force_unaggregated,
        "loan_payment_to_date": loan.loan_payment_to_date,
        "schedule_c": schedule_c_id,
        "memo_text": memo_id,
        "contact_1_id": loan.contact_1_id,
        "contact_2_id": loan.contact_2_id,
        "contact_3_id": loan.contact_3_id,
        "committee_account_id": loan.committee_account_id,
        # The loan_id should point to the original loan transaction
        # even if the loan is pulled forward multiple times.
        "loan_id": loan.loan_id or loan.id,
    }
    new_loan = Transaction.objects.create(**loan_data)
    new_loan.reports.add(report)


@silk_profile(name="carry_forward_loan")
def carry_forward_loan(loan, report):
    # force evaluation of lazy query. if not, the loan.children
    # will be a different queryset after the copy is saved
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

    # for child in original_children:
    #     print('')
    #     # If child is a guarantor transaction, copy it
    #     # and link it to the new loan
    #     if child.schedule_c2 is not None:
    #         carry_forward_guarantor(report, new_loan, child)
