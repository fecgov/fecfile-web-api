from django.db import models
from django.forms.models import model_to_dict
from decimal import Decimal
from fecfiler.transactions.schedule_d.models import ScheduleD
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

    transaction_copy = copy.deepcopy(model_to_dict(transaction))
    # model_to_dict doesn't copy id
    del transaction_copy["report"]
    del transaction_copy["loan"]
    transactions_to_update = Transaction.objects.filter(
        transaction_id=transaction.transaction_id,
        report_id__in=models.Subquery(future_reports.values("id")),
    )
    transactions_to_update.update(**transaction_copy)

    schedule_d_copy = copy.deepcopy(model_to_dict(transaction.schedule_d))
    # don't update the incurred amount because the debt already exists on
    # this report
    del schedule_d_copy["incurred_amount"]
    schedule_ds_to_update = ScheduleD.objects.filter(
        transaction__schedule_d_id__in=models.Subquery(
            transactions_to_update.values("schedule_d_id")
        )
    )
    schedule_ds_to_update.update(**schedule_d_copy)
