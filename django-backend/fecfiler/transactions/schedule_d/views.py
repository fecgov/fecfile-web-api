from django.db.models import Q, Subquery
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
    current_report = transaction.reports.filter(
        Q(form_3x__isnull=False) | Q(form_3__isnull=False)
    ).first()
    future_reports = current_report.get_future_reports()
    transaction_copy = copy.deepcopy(transaction)
    logger.info(
        f"Pulling debt forward from {current_report.id} "
        f"to {len(future_reports)} reports"
    )
    for report in future_reports:
        carry_forward_debt(transaction_copy, report)


def update_in_future_reports(transaction):
    future_reports = (
        transaction.reports.filter(Q(form_3x__isnull=False) | Q(form_3__isnull=False))
        .first()
        .get_future_reports()
    )

    transaction_copy = copy.deepcopy(model_to_dict(transaction))
    # model_to_dict doesn't copy id
    del transaction_copy["reports"]
    del transaction_copy["loan"]
    transactions_to_update = Transaction.objects.filter(
        transaction_id=transaction.transaction_id,
        reports__in=Subquery(future_reports.values("id")),
    )
    # Capture old snapshots for delta-based aggregate updates before bulk update
    from fecfiler.transactions.aggregate_service import (
        update_aggregates_for_affected_transactions,
        calculate_effective_amount,
    )

    pre_update_instances = list(
        Transaction.objects.filter(
            transaction_id=transaction.transaction_id,
            reports__in=Subquery(future_reports.values("id")),
        ).select_related(
            "schedule_a",
            "schedule_b",
            "schedule_c",
            "schedule_e",
            "contact_2",
        )
    )

    old_snapshots_by_id = {}
    for inst in pre_update_instances:
        try:
            eff = calculate_effective_amount(inst)
        except Exception:
            eff = None
        snap = {
            "schedule": inst.get_schedule_name(),
            "contact_1_id": inst.contact_1_id,
            "aggregation_group": inst.aggregation_group,
            "committee_account_id": inst.committee_account_id,
            "date": inst.get_date(),
            "created": inst.created,
            "effective_amount": eff,
        }
        if inst.schedule_e_id and getattr(inst, "contact_2", None):
            snap.update(
                {
                    "election_code": inst.schedule_e.election_code,
                    "candidate_office": inst.contact_2.candidate_office,
                    "candidate_state": inst.contact_2.candidate_state,
                    "candidate_district": inst.contact_2.candidate_district,
                }
            )
        old_snapshots_by_id[str(inst.id)] = snap

    transactions_to_update.update(**transaction_copy)

    schedule_d_copy = copy.deepcopy(model_to_dict(transaction.schedule_d))
    # don't update the incurred amount because the debt already exists on
    # this report
    del schedule_d_copy["incurred_amount"]
    schedule_ds_to_update = ScheduleD.objects.filter(
        transaction__schedule_d_id__in=Subquery(
            transactions_to_update.values("schedule_d_id")
        )
    )
    schedule_ds_to_update.update(**schedule_d_copy)

    # Invoke signals-free aggregation service for each updated transaction
    for tx_id_str, old_snap in old_snapshots_by_id.items():
        try:
            updated_inst = Transaction.objects.get(id=tx_id_str)
            update_aggregates_for_affected_transactions(
                updated_inst, "update", old_snapshot=old_snap
            )
        except Transaction.DoesNotExist:
            continue
