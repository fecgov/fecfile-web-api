from fecfiler.contacts.models import Contact
from django.db.models import Q


def add_org_ind_contact(data, contact: Contact, identifier: str):
    data[f"{identifier}_organization_name"] = contact.name
    data[f"{identifier}_last_name"] = contact.last_name
    data[f"{identifier}_first_name"] = contact.first_name
    data[f"{identifier}_middle_name"] = contact.middle_name
    data[f"{identifier}_prefix"] = contact.prefix
    data[f"{identifier}_suffix"] = contact.suffix
    add_location(data, contact, identifier)


def add_candidate_contact(data, contact: Contact, identifier: str, use_fec: bool):
    # Unfortunately schedule a and b use 'fec_id' whereas c, e, and f use 'id_number'
    fec = f"{identifier}_candidate_" + ("fec_id" if use_fec else "id_number")
    data[fec] = contact.candidate_id
    data[f"{identifier}_candidate_last_name"] = contact.last_name
    data[f"{identifier}_candidate_first_name"] = contact.first_name
    data[f"{identifier}_candidate_middle_name"] = contact.middle_name
    data[f"{identifier}_candidate_prefix"] = contact.prefix
    data[f"{identifier}_candidate_suffix"] = contact.suffix
    data[f"{identifier}_candidate_office"] = contact.candidate_office
    data[f"{identifier}_candidate_district"] = contact.candidate_district
    data[f"{identifier}_candidate_state"] = contact.candidate_state


def add_committee_contact(data, contact: Contact, identifier: str):
    data[f"{identifier}_committee_id_number"] = contact.committee_id
    data[f"{identifier}_committee_name"] = contact.name
    add_location(data, contact, identifier)


def add_location(data, contact: Contact, identifier: str):
    data[f"{identifier}_street_1"] = contact.street_1
    data[f"{identifier}_street_2"] = contact.street_2
    data[f"{identifier}_city"] = contact.city
    data[f"{identifier}_state"] = contact.state
    data[f"{identifier}_zip"] = contact.zip


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
        Q(contact_2_id=contact_id), Q(schedule_f__general_election_year=election_year)
    )


def get_query_for_aggregation_relationship(
    contact_1_id, contact_2_id, election_year, election_code, state, office, district
):
    if contact_1_id:
        return get_query_for_entity_aggregation(contact_1_id)
    elif contact_2_id:
        return get_query_for_payee_candidate_aggregation(election_year, contact_2_id)
    elif election_code is not None:
        return get_query_for_election_aggregation(election_code, state, office, district)
    return Q()


# Returns the set of transactions whose amounts would factor into an aggregate for a date
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
