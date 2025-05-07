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

def filter_for_previous_transactions(
    queryset,
    transaction_id,
    date,
    aggregation_group,
    contact_1_id=None,
    contact_2_id=None,
    election_code=None,
    election_year=None,
    office=None,
    state=None,
    district=None,
):
    print("DUMP QUERYSET for ", date)
    for transaction in queryset:
        print(transaction.date)
    query = queryset.filter(
        ~Q(id=transaction_id or None),
        Q(date__year=date.year),
        Q(date__lte=date),
        Q(aggregation_group=aggregation_group),
    )
    if contact_1_id:
        query = query.filter(Q(contact_1_id=contact_1_id))
    elif contact_2_id:
        query = query.filter(
            Q(contact_2_id=contact_2_id),
            Q(schedule_f__general_election_year=election_year)
        )
    else:
        query = query.filter(
            Q(schedule_e__election_code=election_code),
            Q(contact_2__candidate_office=office),
            Q(contact_2__candidate_state=state),
            Q(contact_2__candidate_district=district),
        )

    original_transaction = None
    if transaction_id:
        original_transaction = queryset.get(id=transaction_id)
        query = query.filter(
            Q(created__lt=original_transaction.created) | ~Q(date=date)
        )

    query = query.order_by("-date", "-created")
    return query