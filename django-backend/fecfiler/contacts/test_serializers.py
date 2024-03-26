from django.test import TestCase
from .models import Contact
from .serializers import ContactSerializer
from rest_framework.request import HttpRequest, Request
from fecfiler.user.models import User


class ContactSerializerTestCase(TestCase):
    fixtures = ["C01234567_user_and_committee"]

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
            "telephone": "+1 1234567890",
        }

        self.invalid_contact = {
            "type": Contact.ContactType.INDIVIDUAL,
            "last_name": "Last",
            "first_name": "First",
            "street_1": "Street",
            "city": "City",
            "country": "USA",
        }

        self.mock_request = Request(HttpRequest())
        self.mock_request.user = User.objects.get(
            id="12345678-aaaa-bbbb-cccc-111122223333"
        )
        self.mock_request.session = {
            "committee_uuid": "11111111-2222-3333-4444-555555555555",
            "committee_id": "C01234567",
        }

    def test_serializer_validate(self):
        valid_serializer = ContactSerializer(
            data=self.valid_contact,
            context={"request": self.mock_request},
        )
        self.assertTrue(valid_serializer.is_valid(raise_exception=True))
        invalid_serializer = ContactSerializer(
            data=self.invalid_contact,
            context={"request": self.mock_request},
        )
        self.assertFalse(invalid_serializer.is_valid())
        self.assertIsNotNone(invalid_serializer.errors["state"])
        self.assertIsNotNone(invalid_serializer.errors["zip"])

    def test_read_only_fields(self):
        update = self.valid_contact.copy()
        update["deleted"] = "2022-03-24T15:24:53.865149-04:00"
        update["last_name"] = "Newlastname"
        contact_serializer = ContactSerializer(
            data=update, context={"request": self.mock_request}
        )
        self.assertTrue(contact_serializer.is_valid(raise_exception=True))
        self.assertEquals(contact_serializer.validated_data["last_name"], "Newlastname")
        self.assertIsNone(contact_serializer.validated_data.get("deleted"))
