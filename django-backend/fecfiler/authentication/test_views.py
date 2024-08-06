from django.test import RequestFactory, TestCase
from django.contrib.auth import get_user_model
from fecfiler.authentication.views import (
    handle_invalid_login,
    handle_valid_login,
)

UserModel = get_user_model()


class AuthenticationTest(TestCase):
    fixtures = ["C01234567_user_and_committee"]
    user = None

    def setUp(self):
        self.user = UserModel.objects.get(id="12345678-aaaa-bbbb-cccc-111122223333")
        self.factory = RequestFactory()

    def test_invalid_login(self):
        resp = handle_invalid_login("random_username")
        self.assertEqual(resp.status_code, 401)

    def test_valid_login(self):
        resp = handle_valid_login(self.user)
        self.assertEqual(resp.status_code, 200)
