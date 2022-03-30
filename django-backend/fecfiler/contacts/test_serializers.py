from django.test import TestCase
from django.core.exceptions import ValidationError
from .models import Contact
from .serializers import ContactSerializer


class ContactSerializerTestCase(TestCase):
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
        )

        self.invalid_contact = Contact(
            type=Contact.ContactType.INDIVIDUAL,
            last_name="Last",
            first_name="First",
            street_1="Street",
            city="City",
        )

    def test_serializer_validate(self):
        valid_data = ContactSerializer(self.valid_contact).data
        self.assertTrue(
            ContactSerializer(data=valid_data).is_valid(raise_exception=True)
        )
        invalid_data = ContactSerializer(self.invalid_contact).data
        invalid_serializer = ContactSerializer(data=invalid_data)
        self.assertFalse(invalid_serializer.is_valid())
        self.assertIsNotNone(invalid_serializer.errors["state"])
        self.assertIsNotNone(invalid_serializer.errors["zip"])
        self.assertIsNotNone(invalid_serializer.errors["country"])
