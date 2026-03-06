"""
Query helpers for aggregation calculations.

These functions build reusable query predicates and filters.
"""

from django.db.models import Q


def get_query_for_earlier_in_same_year(date):
    return Q(
        Q(date__year=date.year),
        Q(date__lte=date),
    )


def get_query_for_earlier_in_same_day(queryset, transaction_id, date):
    if transaction_id:
        original_transaction = queryset.filter(id=transaction_id).first()
        if original_transaction is not None:
            return Q(created__lt=original_transaction.created) | ~Q(date=date)
    return Q()


def get_query_for_entity_aggregation(contact_id):
    return Q(contact_1_id=contact_id)


def get_query_for_election_aggregation(election_code, state, office, district):
    return Q(
        Q(schedule_e__election_code=election_code),
        Q(contact_2__candidate_office=office),
        Q(contact_2__candidate_state=state),
        Q(contact_2__candidate_district=district),
    )


def get_query_for_payee_candidate_aggregation(election_year, contact_id):
    return Q(
        Q(contact_2_id=contact_id),
        Q(schedule_f__general_election_year=election_year)
    )


def get_query_for_aggregation_relationship(
    contact_1_id,
    contact_2_id,
    election_year,
    election_code,
    state,
    office,
    district,
):
    if contact_1_id:
        return get_query_for_entity_aggregation(contact_1_id)
    elif contact_2_id:
        return get_query_for_payee_candidate_aggregation(election_year, contact_2_id)
    elif election_code is not None:
        return get_query_for_election_aggregation(election_code, state, office, district)
    return Q()


def filter_queryset_for_previous_transactions_in_aggregation(
    queryset,
    date,
    aggregation_group,
    transaction_id=None,
    contact_1_id=None,
    contact_2_id=None,
    election_code=None,
    election_year=None,
    office=None,
    state=None,
    district=None,
):
    """Get transactions whose amounts factor into an aggregate for a date."""
    previous_transactions_in_aggregation = queryset.filter(
        ~Q(id=transaction_id or None),  # Filter out the initial transaction
        Q(aggregation_group=aggregation_group),  # Only transactions in same group
        get_query_for_earlier_in_same_year(date),
        get_query_for_earlier_in_same_day(queryset, transaction_id, date),
        get_query_for_aggregation_relationship(
            contact_1_id,
            contact_2_id,
            election_year,
            election_code,
            state,
            office,
            district,
        ),
    )

    return previous_transactions_in_aggregation.order_by("-date", "-created")
