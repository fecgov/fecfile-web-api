"""
Aggregation preparation helpers.

Contains snapshot and effective amount utilities.
"""

from decimal import Decimal
from typing import Optional

from .managers import schedule_b_refunds


def create_old_snapshot(transaction, effective_amount):
    """Snapshot transaction state for aggregate updates."""
    old_snapshot = {
        "schedule": transaction.get_schedule_name(),
        "contact_1_id": transaction.contact_1_id,
        "aggregation_group": transaction.aggregation_group,
        "committee_account_id": transaction.committee_account_id,
        "date": transaction.get_date(),
        "created": transaction.created,
        "effective_amount": effective_amount,
        "force_itemized": transaction.force_itemized,
        "force_unaggregated": transaction.force_unaggregated,
        "memo_code": transaction.memo_code,
        "reatt_redes_id": transaction.reatt_redes_id,
    }
    if transaction.schedule_e and transaction.contact_2:
        old_snapshot.update(
            {
                "election_code": transaction.schedule_e.election_code,
                "candidate_office": transaction.contact_2.candidate_office,
                "candidate_state": transaction.contact_2.candidate_state,
                "candidate_district": transaction.contact_2.candidate_district,
            }
        )
    if transaction.schedule_f and transaction.contact_2:
        old_snapshot.update(
            {
                "contact_2_id": transaction.contact_2_id,
                "election_year": transaction.schedule_f.general_election_year,
            }
        )
    return old_snapshot


def _get_schedule_amount(transaction) -> Optional[Decimal]:
    """
    Extract the base amount from related schedule.

    Args:
        transaction: Transaction instance

    Returns:
        Decimal amount from the transaction's schedule, or None if not found
    """
    schedule_map = {
        "schedule_a": "contribution_amount",
        "schedule_b": "expenditure_amount",
        "schedule_c2": "guaranteed_amount",
        "schedule_d": "incurred_amount",
        "schedule_e": "expenditure_amount",
        "schedule_f": "expenditure_amount",
    }

    for schedule_name, amount_field in schedule_map.items():
        schedule = getattr(transaction, schedule_name, None)
        if schedule:
            return getattr(schedule, amount_field, None)

    if transaction.debt and transaction.debt.schedule_d:
        return transaction.debt.schedule_d.incurred_amount

    return None


def calculate_effective_amount(transaction) -> Decimal:
    """
    Calculate the effective amount for a transaction.

    The effective amount is used for aggregation calculations and differs from
    the transaction amount for certain transaction types (e.g., refunds are
    negated) and for certain schedules (e.g., Schedule C has no effective amount).

    Args:
        transaction: Transaction instance

    Returns:
        Decimal: The effective amount for aggregation
    """
    # Schedule C transactions have no effective amount for aggregation
    if transaction.schedule_c_id is not None:
        return Decimal(0)

    # Get the base amount from related schedule
    amount = _get_schedule_amount(transaction)

    if amount is None:
        return Decimal(0)

    # Ensure Decimal type for downstream arithmetic before any operations
    if not isinstance(amount, Decimal):
        amount = Decimal(str(amount))

    # Refunds are negated
    if transaction.transaction_type_identifier in schedule_b_refunds:
        amount = amount * Decimal(-1)

    return amount


def _get_calendar_year_from_date(date_obj) -> int:
    """
    Parse calendar year from date object or date string in YYYY-MM-DD format.

    Args:
        date_obj: Date object with .year attribute or date string

    Returns:
        Integer year value
    """
    return date_obj.year if hasattr(date_obj, "year") else int(str(date_obj)[:4])
