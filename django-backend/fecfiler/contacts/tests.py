from django.test import TestCase
from django.core.exceptions import ValidationError
from .models import Contact


class F3XTestCase(TestCase):
    fixtures = ['test_contacts']

    def setUp(self):
        self.valid_contact = Contact(
            type=Contact.ContactType.INDIVIDUAL,
            last_name="Last",
            first_name="First",
            street="Street",
            city="City",
            state="State",
            zip="123456789",
            country="Country"
        )

        self.invalid_contact = Contact(
            type=Contact.ContactType.INDIVIDUAL,
            last_name="Last",
            first_name="First",
            street="Street",
            city="City",
        )

    def test_get_contact(self):
        contact = Contact.objects.get(last_name="Lastname")
        self.assertEquals(contact.type, Contact.ContactType.INDIVIDUAL)

    def test_full_clean(self):
        self.valid_contact.full_clean()
        self.assertRaises(ValidationError, self.invalid_contact.full_clean)

    def test_save_and_delete(self):
        self.valid_contact.save()
        contact_from_db = Contact.objects.get(last_name="Last")
        self.assertIsInstance(f3x_summary_from_db, Contact)
        self.assertEquals(contact_from_db.first_name, "First")
        contact_from_db.delete()
        self.assertRaises(
            Contact.DoesNotExist,
            Contact.objects.get,
            first_name="First"
        )

        soft_deleted_contact = Contact.all_objects.get(last_name="Last")
        self.assertEquals(soft_deleted_contact.first_name, "First")
        self.assertIsNotNone(soft_deleted_contact.deleted)
        soft_deleted_contact.hard_delete()
        self.assertRaises(Contact.DoesNotExist, Contact.all_objects.get, last_name="Last")
