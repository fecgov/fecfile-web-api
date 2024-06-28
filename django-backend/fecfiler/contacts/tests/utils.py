from ..models import Contact


def create_test_individual_contact(last_name, first_name, committee_account_id):
    contact = Contact.objects.create(
        type=Contact.ContactType.INDIVIDUAL,
        last_name=last_name,
        first_name=first_name,
        committee_account_id=committee_account_id,
    )
    return contact


def create_test_candidate_contact(
    last_name,
    first_name,
    committee_account_id,
    candidate_id,
    candidate_office,
    candidate_state,
    candidate_district,
):
    contact = Contact.objects.create(
        type=Contact.ContactType.CANDIDATE,
        last_name=last_name,
        first_name=first_name,
        committee_account_id=committee_account_id,
        candidate_id=candidate_id,
        candidate_office=candidate_office,
        candidate_state=candidate_state,
        candidate_district=candidate_district,
    )
    return contact
