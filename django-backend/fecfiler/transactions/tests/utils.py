from django.db.models import Model
from fecfiler.transactions.models import Transaction
from fecfiler.transactions.schedule_a.models import ScheduleA
from fecfiler.transactions.schedule_b.models import ScheduleB
from fecfiler.transactions.schedule_c.models import ScheduleC
from fecfiler.transactions.schedule_c1.models import ScheduleC1
from fecfiler.transactions.schedule_c2.models import ScheduleC2
from fecfiler.transactions.schedule_d.models import ScheduleD
from fecfiler.transactions.schedule_e.models import ScheduleE


def create_schedule_a(
    type, committee, contact, date, amount, group="GENERAL", form_type="SA11I"
):
    return create_test_transaction(
        type,
        ScheduleA,
        committee,
        contact_1=contact,
        group=group,
        schedule_data={"contribution_date": date, "contribution_amount": amount},
        transaction_data={"_form_type": form_type},
    )


def create_schedule_b(
    type, committee, contact, date, amount, group="GENERAL", form_type="SB"
):
    return create_test_transaction(
        type,
        ScheduleA,
        committee,
        contact_1=contact,
        group=group,
        schedule_data={"contribution_date": date, "contribution_amount": amount},
        transaction_data={"_form_type": form_type},
    )


def create_ie(committee, contact, date, amount, code):
    return create_test_transaction(
        "INDEPENDENT_EXPENDITURE",
        ScheduleE,
        committee,
        contact_2=contact,
        schedule_data={
            "disbursement_date": date,
            "expenditure_amount": amount,
            "election_code": code,
        },
    )


def create_debt(committee, contact, incurred_amount):
    return create_test_transaction(
        "DEBT_OWED_BY_COMMITTEE",
        ScheduleD,
        committee,
        contact_1=contact,
        schedule_data={"incurred_amount": incurred_amount},
    )


def create_test_transaction(
    type,
    schedule,
    committee,
    contact_1=None,
    contact_2=None,
    group=None,
    schedule_data=None,
    transaction_data=None,
):
    schedule_object = create_schedule(schedule, schedule_data)
    transaction = Transaction.objects.create(
        transaction_type_identifier=type,
        committee_account=committee,
        contact_1=contact_1,
        contact_2=contact_2,
        aggregation_group=group,
        **{SCHEDULE_CLASS_TO_FIELD[schedule]: schedule_object},
        **(transaction_data or {})
    )
    return transaction


def create_schedule(schedule: Model, data):
    return schedule.objects.create(**data)


SCHEDULE_CLASS_TO_FIELD = {
    ScheduleA: "schedule_a",
    ScheduleB: "schedule_b",
    ScheduleC: "schedule_c",
    ScheduleC1: "schedule_c1",
    ScheduleC2: "schedule_c2",
    ScheduleD: "schedule_d",
    ScheduleE: "schedule_e",
}
