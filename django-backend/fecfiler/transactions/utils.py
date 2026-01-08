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
