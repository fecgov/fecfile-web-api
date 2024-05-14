from ..models import Contact


def create_test_individual_contact(last_name, first_name, committee_account_id):
    contact = Contact.objects.create(
        type=Contact.ContactType.INDIVIDUAL,
        last_name=last_name,
        first_name=first_name,
        committee_account_id=committee_account_id,
    )
    return contact
