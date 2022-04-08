from django.test import TestCase
from .models import Contact
from .serializers import ContactSerializer


class ContactSerializerTestCase(TestCase):
    fixtures = ["test_committee_accounts"]

    def setUp(self):
        self.valid_contact = {
            "type": Contact.ContactType.INDIVIDUAL,
            "last_name": "Last",
            "first_name": "First",
            "street_1": "Street",
            "city": "City",
            "state": "St",
            "zip": "123456789",
            "country": "Country",
        }

        self.invalid_contact = {
            "type": Contact.ContactType.INDIVIDUAL,
            "last_name": "Last",
            "first_name": "First",
            "street_1": "Street",
            "city": "City",
        }

    def test_serializer_validate(self):
        valid_serializer = ContactSerializer(
            data=self.valid_contact,
            context={"request": {"user": {"cmtee_id": "C00277616"}}},
        )
        self.assertTrue(valid_serializer.is_valid(raise_exception=True))
        invalid_serializer = ContactSerializer(
            data=self.invalid_contact,
            context={"request": {"user": {"cmtee_id": "C00277616"}}},
        )
        self.assertFalse(invalid_serializer.is_valid())
        self.assertIsNotNone(invalid_serializer.errors["state"])
        self.assertIsNotNone(invalid_serializer.errors["zip"])
        self.assertIsNotNone(invalid_serializer.errors["country"])

    def test_read_only_fields(self):
        update = self.valid_contact.copy()
        update["deleted"] = "2022-03-24T15:24:53.865149-04:00"
        update["last_name"] = "Newlastname"
        contact_serializer = ContactSerializer(
            data=update, context={"request": {"user": {"cmtee_id": "C00277616"}}}
        )
        self.assertTrue(contact_serializer.is_valid(raise_exception=True))
        self.assertEquals(contact_serializer.validated_data["last_name"], "Newlastname")
        self.assertIsNone(contact_serializer.validated_data.get("deleted"))
