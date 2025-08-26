from django.test import TestCase
from fecfiler.user.models import User
from fecfiler.user.utils import get_user_by_email_or_id
from uuid import uuid4

class UserUtilsTestCase(TestCase):
    def setUp(self):
        self.user_1 = User.objects.create_user(
            email="test_user_1@test.com", user_id=str(uuid4())
        )
        self.user_2 = User.objects.create_user(
            email="test_user_2@test.com", user_id=str(uuid4())
        )
        self.user_3 = User.objects.create_user(
            email="test_user_3@test.com", user_id=str(uuid4())
        )

    def test_get_user_with_invalid_strings(self):
        self.assertEqual(get_user_by_email_or_id(""), None)
        self.assertEqual(get_user_by_email_or_id("test_user_4@test.com"), None)
        self.assertEqual(get_user_by_email_or_id("test_user_1ATtest.com"), None)
        self.assertEqual(get_user_by_email_or_id("-"), None)
        self.assertEqual(get_user_by_email_or_id(
            str(self.user_1.id).replace("-", "")),
            None
        )

    def test_get_user_with_valid_strings(self):
        self.assertEqual(get_user_by_email_or_id(str(self.user_1.id)), self.user_1)
        self.assertEqual(get_user_by_email_or_id(self.user_1.email), self.user_1)
        self.assertEqual(get_user_by_email_or_id(self.user_2.email), self.user_2)
        self.assertEqual(get_user_by_email_or_id(str(self.user_3.id)), self.user_3)