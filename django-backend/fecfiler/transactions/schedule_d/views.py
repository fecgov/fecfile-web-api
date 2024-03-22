from django.db import models
from django.forms.models import model_to_dict
from fecfiler.transactions.schedule_d.models import ScheduleD
from fecfiler.transactions.schedule_d.utils import carry_forward_debt
import copy
from fecfiler.transactions.models import Transaction
import structlog

logger = structlog.get_logger(__name__)


def save_hook(transaction: Transaction, is_existing):
    if not is_existing:
        create_in_future_reports(transaction)
    else:
        update_in_future_reports(transaction)


def create_in_future_reports(transaction):
    current_report = transaction.reports.filter(form_3x__isnull=False).first()
    future_reports = current_report.get_future_in_progress_reports()
    transaction_copy = copy.deepcopy(transaction)
    logger.info(
        f"Pulling debt forward from {current_report.id} "
        f"to {len(future_reports)} reports"
    )
    for report in future_reports:
        carry_forward_debt(transaction_copy, report)


def update_in_future_reports(transaction):
    future_reports = transaction.reports.filter(
        form_3x__isnull=False).first().get_future_in_progress_reports()

    transaction_copy = copy.deepcopy(model_to_dict(transaction))
    # model_to_dict doesn't copy id
    del transaction_copy["reports"]
    del transaction_copy["loan"]
    transactions_to_update = Transaction.objects.filter(
        transaction_id=transaction.transaction_id,
        reports__in=models.Subquery(future_reports.values("id")),
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
