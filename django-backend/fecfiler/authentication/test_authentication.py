from django.test import RequestFactory, TestCase
from fecfiler.authentication.models import Account
from fecfiler.authentication.authenticate_login import (
    update_last_login_time,
    handle_invalid_login,
    handle_valid_login,
)


class TestAuthentication(TestCase):
    fixtures = ["test_accounts"]
    acc = None

    def setUp(self):
        self.factory = RequestFactory()
        self.acc = Account.objects.get(email="unit_tester@test.com")

    def test_update_login_time(self):
        prev_time = self.acc.last_login
        update_last_login_time(self.acc)
        self.assertNotEqual(self.acc.last_login, prev_time)

    def test_invalid_login(self):
        resp = handle_invalid_login("random_username")
        self.assertEqual(resp.status_code, 401)

    def test_valid_login(self):
        resp = handle_valid_login(self.acc)
        self.assertEqual(resp.status_code, 200)
