from django.test import TestCase
from ..models import Contact


class ContactTestCase(TestCase):
    fixtures = ["C01234567_user_and_committee", "test_contacts"]

    def setUp(self):
        self.valid_contact = Contact(
            type=Contact.ContactType.INDIVIDUAL,
            last_name="Last",
            first_name="First",
            street_1="Street",
            city="City",
            state="St",
            zip="123456789",
            country="Country",
            committee_account_id="11111111-2222-3333-4444-555555555555",
        )

    def test_get_contact(self):
        contact = Contact.objects.get(last_name="Lastname")
        self.assertEqual(contact.type, Contact.ContactType.INDIVIDUAL)

    def test_save_and_delete(self):
        self.valid_contact.save()
        contact_from_db = Contact.objects.get(last_name="Last")
        self.assertIsInstance(contact_from_db, Contact)
        self.assertEqual(contact_from_db.first_name, "First")
        contact_from_db.delete()
        self.assertRaises(Contact.DoesNotExist, Contact.objects.get, first_name="First")

        soft_deleted_contact = Contact.all_objects.get(last_name="Last")
        self.assertEqual(soft_deleted_contact.first_name, "First")
        self.assertIsNotNone(soft_deleted_contact.deleted)
        soft_deleted_contact.hard_delete()
        self.assertRaises(Contact.DoesNotExist, Contact.all_objects.get, last_name="Last")
