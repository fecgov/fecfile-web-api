from django.db import models
from fecfiler.transactions.schedule_c.models import ScheduleC
from fecfiler.transactions.models import Transaction
from fecfiler.memo_text.models import MemoText
from fecfiler.shared.utilities import get_model_data
import copy


def save_hook(transaction: Transaction, is_existing):
    if not transaction.memo_code:
        if not is_existing:
            create_in_future_reports(transaction)
        else:
            update_in_future_reports(transaction)


def create_in_future_reports(transaction: Transaction):
    future_reports = transaction.report.get_future_in_progress_reports()
    transaction_copy = copy.deepcopy(transaction)
    for report in future_reports:
        report.pull_forward_loan(transaction_copy)


def update_in_future_reports(transaction: Transaction):
    future_reports = transaction.report.get_future_in_progress_reports()

    transaction_data = get_model_data(transaction, Transaction)
    del transaction_data["id"]
    transactions_to_update = Transaction.objects.filter(
        transaction_id=transaction.transaction_id,
        report_id__in=models.Subquery(future_reports.values("id")),
    )
    # transaction_data["contact_1_id"] = (transaction_data.pop("contact_1") or {}).pop(
    #     "id", transaction_data.get("contact_1_id")
    # )
    # transaction_data["contact_2_id"] = (transaction_data.pop("contact_2") or {}).pop(
    #     "id", transaction_data.get("contact_2_id")
    # )
    # transaction_data["contact_3_id"] = (transaction_data.pop("contact_3") or {}).pop(
    #     "id", transaction_data.get("contact_3_id")
    # )
    # print(f"AHOYYOHA:{transaction_data}")
    transactions_to_update.update(**transaction_data)

    schedule_c_data = get_model_data(transaction, ScheduleC)
    del schedule_c_data["id"]
    schedule_cs_to_update = ScheduleC.objects.filter(
        transaction__schedule_c_id__in=models.Subquery(
            transactions_to_update.values("schedule_c_id")
        )
    )
    schedule_cs_to_update.update(**schedule_c_data)

    update_memo_text_in_future_reports(
        transaction, transaction_data, transactions_to_update
    )


def update_memo_text_in_future_reports(
    transaction, transaction_data: dict, transactions_to_update
):
    memo_text_id = transaction_data.get("memo_text_id")
    if not memo_text_id:
        for memo_text in MemoText.objects.filter(
            transaction__memo_text_id__in=models.Subquery(
                transactions_to_update.values("memo_text_id")
            )
        ):
            memo_text.delete()
        transactions_to_update.update(**{"memo_text_id": None})
    else:
        MemoText.objects.filter(
            transaction__memo_text_id__in=models.Subquery(
                transactions_to_update.values("memo_text_id")
            )
        ).update(**{"text4000": transaction.memo_text.text4000})

        for transaction_to_update in transactions_to_update.filter(
            memo_text_id__isnull=True
        ):
            new_memo_text = MemoText.objects.create(
                **{
                    "rec_type": "TEXT",
                    "transaction_id_number": transaction_to_update.transaction_id,
                    "text4000": transaction.memo_text.text4000,
                    "report_id": transaction.report.id,
                    "committee_account_id": transaction_to_update.committee_account.id,
                    "transaction_uuid": transaction_to_update.id,
                    "is_report_level_memo": False,
                }
            )
            Transaction.objects.filter(id=transaction_to_update.id).update(
                **{"memo_text": new_memo_text}
            )
