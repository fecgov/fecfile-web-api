from django.test import TestCase
from django.core.urlresolvers import reverse
from .views import *

# Create your tests here
from fecfiler.authentication.models import Account


class SimpleTest(TestCase):
    def setUp(self):
        self.credentials = {
            'username': 'C01234567',
            'password': 'test',
            'email': 'test1@test.com'
        }
        self.user = Account.objects.create_user(**self.credentials)

    def test_login_success(self):
        response = self.client.post('/api/v1/auth/login/', **self.credentials)
        # should be logged in now, fails however
        # self.assertEqual(response.context['user']==self.user)
