from django.db import models
from fecfiler.transactions.models import Transaction
from fecfiler.memo_text.models import MemoText
from fecfiler.shared.utilities import get_model_data
from fecfiler.transactions.schedule_c2.models import ScheduleC2
import copy


def save_hook(transaction: Transaction, is_existing):
    if not transaction.parent_transaction.memo_code:
        if not is_existing:
            create_in_future_reports(transaction)
        else:
            update_in_future_reports(transaction)


def create_in_future_reports(transaction):
    future_reports = transaction.report.get_future_in_progress_reports()
    for report in future_reports:
        loan = Transaction.objects.get(
            report_id=report.id, loan_id=transaction.parent_transaction.id
        )
        report.pull_forward_loan_guarantor(copy.deepcopy(transaction), loan)


def update_in_future_reports(transaction):
    future_reports = transaction.report.get_future_in_progress_reports()

    transaction_data = get_model_data(transaction, Transaction)
    del transaction_data["id"]
    transactions_to_update = Transaction.objects.filter(
        transaction_id=transaction.transaction_id,
        report_id__in=models.Subquery(future_reports.values("id")),
    )
    transactions_to_update.update(**transaction_data)

    schedule_c2_data = get_model_data(transaction, ScheduleC2)
    del schedule_c2_data["id"]
    schedule_c2s_to_update = ScheduleC2.objects.filter(
        transaction__schedule_c2_id__in=models.Subquery(
            transactions_to_update.values("schedule_c2_id")
        )
    )
    schedule_c2s_to_update.update(**schedule_c2_data)

    memo_text_data = get_model_data(transaction, MemoText)
    del memo_text_data["id"]
    memo_text_to_update = MemoText.objects.filter(
        transaction__memo_text_id__in=models.Subquery(
            transactions_to_update.values("memo_text_id")
        )
    )
    memo_text_to_update.update(**memo_text_data)
