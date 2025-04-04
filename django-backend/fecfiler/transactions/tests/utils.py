from datetime import datetime
from decimal import Decimal
from uuid import UUID
from django.db.models import Model
from fecfiler.transactions.models import Transaction
from fecfiler.transactions.schedule_a.models import ScheduleA
from fecfiler.transactions.schedule_b.models import ScheduleB
from fecfiler.transactions.schedule_c.models import ScheduleC
from fecfiler.transactions.schedule_c1.models import ScheduleC1
from fecfiler.transactions.schedule_c2.models import ScheduleC2
from fecfiler.transactions.schedule_d.models import ScheduleD
from fecfiler.transactions.schedule_e.models import ScheduleE
from fecfiler.transactions.schedule_f.models import ScheduleF
from fecfiler.contacts.models import Contact
from fecfiler.reports.models import ReportTransaction
from fecfiler.memo_text.models import MemoText
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.reports.models import Report


def create_schedule_a(
    type: str,
    committee: CommitteeAccount,
    contact: Contact | None,
    date: str | None,
    amount: str | int | float,
    group: str = "GENERAL",
    form_type: str = "SA11AI",
    memo_code: bool = False,
    itemized: bool | None = None,
    report: Report | None = None,
    parent_id: UUID | None = None,
    purpose_description: str | None = None,
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
            "contribution_purpose_descrip": purpose_description,
        },
        transaction_data=transaction_data,
    )


def create_schedule_b(
    type: str,
    committee: CommitteeAccount,
    contact: Contact,
    date: str,
    amount: str,
    group: str = "GENERAL",
    form_type: str = "SB",
    memo_code: bool = False,
    report: Report | None = None,
    loan_id: UUID | None = None,
    debt_id: UUID | None = None,
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
            "debt_id": debt_id,
        },
    )


def create_ie(
    committee: CommitteeAccount,
    contact: Contact,
    disbursement_date: str,
    dissemination_date: str,
    date_signed: str,
    amount: str,
    code: str,
    candidate: Contact,
    memo_code: bool = False,
    report: Report | None = None,
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
            "date_signed": date_signed,
        },
        transaction_data={
            "_form_type": "SE",
            "memo_code": memo_code,
        },
    )


def create_debt(
    committee: CommitteeAccount,
    contact: Contact,
    incurred_amount: Decimal,
    form_type: str = "SD9",
    type: str = "DEBT_OWED_BY_COMMITTEE",
    report: Report | None = None,
):
    return create_test_transaction(
        type,
        ScheduleD,
        committee,
        contact_1=contact,
        report=report,
        schedule_data={
            "incurred_amount": incurred_amount,
            "report_coverage_from_date": (
                report.coverage_from_date if report is not None else None
            ),
        },
        transaction_data={"_form_type": form_type},
    )


def create_loan(
    committee: CommitteeAccount,
    contact: Contact,
    loan_amount: Decimal,
    loan_due_date: str | datetime,
    loan_interest_rate: str,
    secured: bool = False,
    type: str = "LOAN_RECEIVED_FROM_INDIVIDUAL",
    form_type: str = "SC/9",
    loan_incurred_date: str | datetime | None = None,
    report: Report | None = None,
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
    committee: CommitteeAccount,
    contact: Contact,
    loan_amount: Decimal,
    loan_due_date: datetime | str,
    loan_interest_rate: str,
    secured: bool = False,
    loan_incurred_date: datetime | str | None = None,
    report: Report | None = None,
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


def create_schedule_f(
    type: str,
    committee: CommitteeAccount,
    contact_1: Contact | None,
    contact_2: Contact | None,
    contact_3: Contact | None,
    contact_4: Contact | None,
    contact_5: Contact | None,
    group: str = "GENERAL",
    form_type: str = "SF",
    memo_code: bool = False,
    schedule_data=None,
    report: Report | None = None,
):
    return create_test_transaction(
        type,
        ScheduleF,
        committee,
        contact_1=contact_1,
        contact_2=contact_2,
        contact_3=contact_3,
        contact_4=contact_4,
        contact_5=contact_5,
        group=group,
        report=report,
        schedule_data=schedule_data,
        transaction_data={
            "_form_type": form_type,
            "memo_code": memo_code,
        },
    )


def create_test_transaction(
    type: str,
    schedule: Model,
    committee: CommitteeAccount,
    contact_1: Contact | None = None,
    contact_2: Contact | None = None,
    contact_3: Contact | None = None,
    contact_4: Contact | None = None,
    contact_5: Contact | None = None,
    group: str | None = None,
    schedule_data=None,
    transaction_data=None,
    report: Report | None = None,
):
    schedule_object = create_schedule(schedule, schedule_data)
    transaction = Transaction.objects.create(
        transaction_type_identifier=type,
        committee_account=committee,
        contact_1=contact_1,
        contact_2=contact_2,
        contact_3=contact_3,
        contact_4=contact_4,
        contact_5=contact_5,
        aggregation_group=group,
        entity_type=getattr(contact_1, "type", None),
        **{SCHEDULE_CLASS_TO_FIELD[schedule]: schedule_object},
        **(transaction_data or {})
    )
    if report:
        create_report_transaction(report, transaction)
    return transaction


def create_schedule(schedule: Model, data):
    return schedule.objects.create(**data)


def create_report_transaction(report: Report, transaction: Transaction):
    if transaction and report:
        return ReportTransaction.objects.create(
            report_id=report.id, transaction_id=transaction.id
        )


def create_transaction_memo(
    committee_account: CommitteeAccount, transaction: Transaction, text4000: str
):
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
    ScheduleF: "schedule_f",
}
