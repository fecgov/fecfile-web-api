from django.db.models import Q, Subquery
from fecfiler.transactions.models import Transaction
from django.forms.models import model_to_dict
from fecfiler.transactions.schedule_c2.models import ScheduleC2
from fecfiler.transactions.schedule_c2.utils import carry_forward_guarantor
import copy


def save_hook(transaction: Transaction, is_existing):
    if not transaction.parent_transaction.memo_code:
        if not is_existing:
            create_in_future_reports(transaction)
        else:
            update_in_future_reports(transaction)


def create_in_future_reports(transaction):
    current_report = transaction.reports.filter(
        Q(form_3x__isnull=False) | Q(form_3__isnull=False)
    ).first()
    future_reports = current_report.get_future_reports()
    for report in future_reports:
        loan_query = Transaction.objects.filter(
            reports__id=report.id, loan_id=transaction.parent_transaction.id
        )
        if loan_query.count():
            carry_forward_guarantor(
                report, loan_query.first(), copy.deepcopy(transaction)
            )


def update_in_future_reports(transaction):
    current_report = transaction.reports.filter(
        Q(form_3x__isnull=False) | Q(form_3__isnull=False)
    ).first()
    future_reports = current_report.get_future_reports()

    transaction_copy = model_to_dict(transaction)
    fields_to_exclude = ["reports", "id", "pk", "parent_transaction", "schedule_c2"]

    for field in fields_to_exclude:
        if field in transaction_copy:
            del transaction_copy[field]

    transactions_to_update = Transaction.objects.filter(
        transaction_id=transaction.transaction_id,
        reports__id__in=Subquery(future_reports.values("id")),
    )

    schedule_c2_copy = model_to_dict(transaction.schedule_c2)
    if "id" in schedule_c2_copy:
        del schedule_c2_copy["id"]
    schedule_c2s_to_update = ScheduleC2.objects.filter(
        transaction__schedule_c2_id__in=Subquery(
            transactions_to_update.values("schedule_c2_id")
        )
    )

    # Capture old snapshots before bulk update
    snapshots = {}
    for t in transactions_to_update.select_related(
        "schedule_c2",
        "contact_1",
        "contact_2",
    ):
        snap = {
            "schedule": t.get_schedule_name(),
            "contact_1_id": t.contact_1_id,
            "aggregation_group": t.aggregation_group,
            "committee_account_id": t.committee_account_id,
            "date": t.get_date(),
            "created": t.created,
        }
        try:
            from fecfiler.transactions.aggregate_service import (
                calculate_effective_amount,
            )
            eff = calculate_effective_amount(t)
            snap.update({"effective_amount": eff})
        except Exception:
            pass
        snapshots[str(t.id)] = snap

    schedule_c2s_to_update.update(**schedule_c2_copy)
    transactions_to_update.update(**transaction_copy)

    # Explicitly invoke aggregation service for updated transactions
    from fecfiler.transactions.aggregate_service import (
        update_aggregates_for_affected_transactions,
    )
    for updated in Transaction.objects.filter(id__in=snapshots.keys()):
        update_aggregates_for_affected_transactions(
            updated, "update", old_snapshot=snapshots[str(updated.id)]
        )
