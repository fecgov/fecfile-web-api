from django.db import models
import uuid
from decimal import Decimal
from fecfiler.transactions.schedule_d.models import ScheduleD
from fecfiler.shared.utilities import get_model_data
import copy

from django.db.models import Q

from fecfiler.transactions.models import Transaction


def save_hook(transaction: Transaction, is_existing):
    if not is_existing:
        if Transaction.objects.filter(
            ~Q(balance_at_close=Decimal(0)) | Q(balance_at_close__isnull=True),
            id=transaction.id,
        ).count():
            create_in_future_reports(transaction)
    else:
        update_in_future_reports(transaction)


def create_in_future_reports(transaction):
    future_reports = transaction.report.get_future_in_progress_reports()
    transaction_copy = copy.deepcopy(transaction)
    for report in future_reports:
        report.pull_forward_debt(transaction_copy)


def update_in_future_reports(transaction):
    future_reports = transaction.report.get_future_in_progress_reports()

    transaction_data = copy.deepcopy(transaction)
    del transaction_data.id
    transactions_to_update = Transaction.objects.filter(
        transaction_id=transaction.transaction_id,
        report_id__in=models.Subquery(future_reports.values("id")),
    )
    transactions_to_update.update(**transaction_data)

    schedule_d_data = copy.deepcopy(transaction)
    del schedule_d_data.id
    schedule_d_data.incurred_amount = 0
    schedule_ds_to_update = ScheduleD.objects.filter(
        transaction__schedule_d_id__in=models.Subquery(
            transactions_to_update.values("schedule_d_id")
        )
    )
    schedule_ds_to_update.update(**schedule_d_data)
