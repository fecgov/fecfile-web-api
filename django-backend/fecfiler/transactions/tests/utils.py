from django.db.models import Model
from fecfiler.transactions.models import Transaction
from fecfiler.transactions.schedule_a.models import ScheduleA
from fecfiler.transactions.schedule_b.models import ScheduleB
from fecfiler.transactions.schedule_c.models import ScheduleC
from fecfiler.transactions.schedule_c1.models import ScheduleC1
from fecfiler.transactions.schedule_c2.models import ScheduleC2
from fecfiler.transactions.schedule_d.models import ScheduleD
from fecfiler.transactions.schedule_e.models import ScheduleE
from fecfiler.contacts.models import Contact
from fecfiler.reports.models import ReportTransaction
from fecfiler.memo_text.models import MemoText


def create_schedule_a(
    type,
    committee,
    contact,
    date,
    amount,
    group="GENERAL",
    form_type="SA11I",
    memo_code=False,
    itemized=False,
    report=None,
    parent_id=None,
    purpose_description=None,
):
    transaction_data = {
        "_form_type": form_type,
        "memo_code": memo_code,
        "force_itemized": itemized,
    }
    if parent_id is not None:
        transaction_data["parent_transaction_id"] = parent_id
    return create_test_transaction(
        type,
        ScheduleA,
        committee,
        contact_1=contact,
        group=group,
        report=report,
        schedule_data={
            "contribution_date": date,
            "contribution_amount": amount,
            "contribution_purpose_descrip": purpose_description
        },
        transaction_data=transaction_data,
    )


def create_schedule_b(
    type,
    committee,
    contact,
    date,
    amount,
    group="GENERAL",
    form_type="SB",
    memo_code=False,
    report=None,
    loan_id=None,
):
    return create_test_transaction(
        type,
        ScheduleB,
        committee,
        contact_1=contact,
        group=group,
        report=report,
        schedule_data={"expenditure_date": date, "expenditure_amount": amount},
        transaction_data={
            "_form_type": form_type,
            "memo_code": memo_code,
            "loan_id": loan_id,
        },
    )


def create_ie(
    committee,
    contact: Contact,
    disbursement_date,
    dissemination_date,
    amount,
    code,
    candidate: Contact,
    memo_code=False,
    report=None,
):
    return create_test_transaction(
        "INDEPENDENT_EXPENDITURE",
        ScheduleE,
        committee,
        contact_1=contact,
        contact_2=candidate,
        report=report,
        group="INDEPENDENT_EXPENDITURE",
        schedule_data={
            "disbursement_date": disbursement_date,
            "dissemination_date": dissemination_date,
            "expenditure_amount": amount,
            "election_code": code,
        },
        transaction_data={
            "_form_type": "SE",
            "memo_code": memo_code,
        },
    )


def create_debt(
    committee,
    contact,
    incurred_amount,
    form_type="SD9",
    type="DEBT_OWED_BY_COMMITTEE",
    report=None,
):
    return create_test_transaction(
        type,
        ScheduleD,
        committee,
        contact_1=contact,
        report=report,
        schedule_data={"incurred_amount": incurred_amount},
        transaction_data={"_form_type": form_type},
    )


def create_loan(
    committee,
    contact,
    loan_amount,
    loan_due_date,
    loan_interest_rate,
    secured=False,
    type="LOAN_RECEIVED_FROM_INDIVIDUAL",
    form_type="SC/9",
    loan_incurred_date=None,
    report=None,
):
    report_coverage_through_date = report.coverage_through_date if report else None
    return create_test_transaction(
        type,
        ScheduleC,
        committee,
        contact_1=contact,
        schedule_data={
            "loan_amount": loan_amount,
            "loan_due_date": loan_due_date,
            "loan_interest_rate": loan_interest_rate,
            "secured": secured,
            "loan_incurred_date": loan_incurred_date,
            "report_coverage_through_date": report_coverage_through_date,
        },
        transaction_data={"_form_type": form_type},
        report=report,
    )


def create_loan_from_bank(
    committee,
    contact,
    loan_amount,
    loan_due_date,
    loan_interest_rate,
    secured=False,
    loan_incurred_date=None,
    report=None,
):
    loan = create_loan(
        committee,
        contact,
        loan_amount,
        loan_due_date,
        loan_interest_rate,
        secured,
        "LOAN_RECEIVED_FROM_BANK",
        "SC/10",
        loan_incurred_date,
        report,
    )
    loan_receipt = create_schedule_a(
        "LOAN_RECEIVED_FROM_BANK_RECEIPT",
        committee,
        contact,
        loan_incurred_date,
        loan_amount,
        report=report,
        parent_id=loan.id,
    )
    loan_agreement = create_test_transaction(
        "C1_LOAN_AGREEMENT",
        ScheduleC1,
        committee,
        contact_1=contact,
        group=None,
        report=report,
        schedule_data={
            "loan_incurred_date": loan_incurred_date,
            "loan_amount": loan_amount,
            "loan_due_date": loan_due_date,
            "loan_interest_rate": loan_interest_rate,
        },
        transaction_data={"_form_type": "SC1/10", "parent_transaction_id": loan.id},
    )
    guarantor = create_test_transaction(
        "C2_LOAN_GUARANTOR",
        ScheduleC2,
        committee,
        contact_1=contact,
        group=None,
        report=report,
        schedule_data={},
        transaction_data={"_form_type": "SC2/10", "parent_transaction_id": loan.id},
    )
    return loan, loan_receipt, loan_agreement, guarantor


def create_test_transaction(
    type,
    schedule,
    committee,
    contact_1=None,
    contact_2=None,
    group=None,
    schedule_data=None,
    transaction_data=None,
    report=None,
):
    schedule_object = create_schedule(schedule, schedule_data)
    transaction = Transaction.objects.create(
        transaction_type_identifier=type,
        committee_account=committee,
        contact_1=contact_1,
        contact_2=contact_2,
        aggregation_group=group,
        entity_type=getattr(contact_1, 'type', None),
        **{SCHEDULE_CLASS_TO_FIELD[schedule]: schedule_object},
        **(transaction_data or {})
    )
    if report:
        create_report_transaction(report, transaction)
    return transaction


def create_schedule(schedule: Model, data):
    return schedule.objects.create(**data)


def create_report_transaction(report, transaction):
    if transaction and report:
        return ReportTransaction.objects.create(
            report_id=report.id, transaction_id=transaction.id
        )


def create_transaction_memo(committee_account, transaction, text4000):
    return MemoText.objects.create(
        rec_type="TEXT",
        text4000=text4000,
        committee_account_id=committee_account.id,
        transaction_uuid=transaction.id,
    )


SCHEDULE_CLASS_TO_FIELD = {
    ScheduleA: "schedule_a",
    ScheduleB: "schedule_b",
    ScheduleC: "schedule_c",
    ScheduleC1: "schedule_c1",
    ScheduleC2: "schedule_c2",
    ScheduleD: "schedule_d",
    ScheduleE: "schedule_e",
}
