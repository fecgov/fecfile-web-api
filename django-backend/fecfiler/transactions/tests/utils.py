from django.test import TestCase
from django.db.models import QuerySet, Model

from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.contacts.models import Contact
from fecfiler.transactions.models import Transaction, Schedule
from fecfiler.transactions.schedule_a.models import ScheduleA
from fecfiler.transactions.schedule_b.models import ScheduleB
from fecfiler.transactions.schedule_c.models import ScheduleC
from fecfiler.transactions.schedule_c1.models import ScheduleC1
from fecfiler.transactions.schedule_c2.models import ScheduleC2
from fecfiler.transactions.schedule_d.models import ScheduleD
from fecfiler.transactions.schedule_e.models import ScheduleE
from fecfiler.transactions.managers import TransactionManager
import uuid
from decimal import Decimal


def create_test_transaction(type, schedule, committee, contact=None, data=None):
    schedule = create_schedule(schedule, data)
    transaction = Transaction.objects.create(
        committee_account=committee,
        contact=contact,
        **{SCHEDULE_CLASS_TO_FIELD[schedule]: schedule}
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
