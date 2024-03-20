from django.db import models
from fecfiler.transactions.models import Transaction
from django.forms.models import model_to_dict
from fecfiler.transactions.schedule_c2.models import ScheduleC2
from fecfiler.transactions.schedule_c2.utils import carry_forward_guarantor
import copy


def save_hook(transaction: Transaction, is_existing):
    print("AHOY SAVE_HOOK: GUARANTOR")
    if not transaction.parent_transaction.memo_code:
        if not is_existing:
            create_in_future_reports(transaction)
        else:
            update_in_future_reports(transaction)


def create_in_future_reports(transaction):
    print("AHOY create_in_future: GUARANTOR")
    future_reports = transaction.report.get_future_in_progress_reports()
    for report in future_reports:
        loan_query = Transaction.objects.filter(
            report_id=report.id, loan_id=transaction.parent_transaction.id
        )
        if loan_query.count():
            carry_forward_guarantor(
                report, loan_query.first(), copy.deepcopy(transaction)
            )


def update_in_future_reports(transaction):
    future_reports = transaction.report.get_future_in_progress_reports()

    transaction_copy = copy.deepcopy(model_to_dict(transaction))
    # model_to_dict doesn't copy id
    del transaction_copy["report"]
    transactions_to_update = Transaction.objects.filter(
        transaction_id=transaction.transaction_id,
        report_id__in=models.Subquery(future_reports.values("id")),
    )
    transactions_to_update.update(**transaction_copy)
    print("foo")

    schedule_c2_copy = copy.deepcopy(model_to_dict(transaction.schedule_c2))
    schedule_c2s_to_update = ScheduleC2.objects.filter(
        transaction__schedule_c2_id__in=models.Subquery(
            transactions_to_update.values("schedule_c2_id")
        )
    )
    schedule_c2s_to_update.update(**schedule_c2_copy)
