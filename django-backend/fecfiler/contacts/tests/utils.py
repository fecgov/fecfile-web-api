from ..models import Contact


def create_test_individual_contact(last_name, first_name, committee_account_id, kwargs={}):
    contact = Contact.objects.create(
        type=Contact.ContactType.INDIVIDUAL,
        last_name=last_name,
        first_name=first_name,
        committee_account_id=committee_account_id,
        **kwargs
    )
    return contact


def create_test_organization_contact(name, committee_account_id, kwargs={}):
    return Contact.objects.create(
        type=Contact.ContactType.ORGANIZATION,
        name=name,
        committee_account_id=committee_account_id,
        **kwargs
    )


def create_test_committee_contact(name, committee_id, committee_account_id, kwargs={}):
    return Contact.objects.create(
        type=Contact.ContactType.COMMITTEE,
        name=name,
        committee_id=committee_id,
        committee_account_id=committee_account_id,
        **kwargs
    )


def create_test_candidate_contact(
    last_name,
    first_name,
    committee_account_id,
    candidate_id,
    candidate_office,
    candidate_state,
    candidate_district,
    kwargs={}
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
        **kwargs
    )
    return contact
