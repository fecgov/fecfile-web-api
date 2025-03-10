from django.test import TestCase
from fecfiler.user.models import User
from django.core.management import call_command
from django.contrib.auth import get_user_model


class DisableUserCommandTest(TestCase):

    def setUp(self):
        self.test_user = User.objects.create(email="test@fec.gov", username="gov")

    def test_disable_user_email(self):
        user_model = get_user_model()

        # get the test user
        user = user_model.objects.get(email=self.test_user.email)
        self.assertTrue(user.is_active)

        # disable the test user
        try:
            call_command("disable_user", email=user.email)
        except Exception as e:
            print(f"Error running command: {e}")

        # re-get the test user
        user = user_model.objects.get(email=self.test_user.email)
        self.assertFalse(user.is_active)

    def test_disable_user_uuid(self):
        user_model = get_user_model()

        # get the test user
        user = user_model.objects.get(username=self.test_user.username)
        self.assertTrue(user.is_active)

        # disable the test user
        try:
            call_command("disable_user", uuid=user.username)
        except Exception as e:
            print(f"Error running command: {e}")

        # re-get the test user
        user = user_model.objects.get(username=self.test_user.username)
        self.assertFalse(user.is_active)
