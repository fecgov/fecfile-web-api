from unittest.mock import patch
from django.test import TestCase
from fecfiler.user.models import User
from django.core.management import call_command
from django.contrib.auth import get_user_model


class DisableUserCommandTest(TestCase):

    def setUp(self):
        self.test_user = User.objects.create(email="test@fec.gov", username="gov")

    def test_disable_user(self):
        User = get_user_model()

        # get the test user
        user = User.objects.get(email=self.test_user.email)
        self.assertTrue(user.is_active)

        # disable the test user
        try:
            call_command("disable_user", user.email)
        except Exception as e:
            print(f"Error running command: {e}")

        # re-get the test user
        user = User.objects.get(email=self.test_user.email)
        self.assertFalse(user.is_active)
