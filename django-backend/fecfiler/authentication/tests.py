import json

from django.test import TestCase
#from django.urls import resolve
#from django.core.urlresolvers import reverse
from .views import *
from rest_framework_jwt.utils import jwt_decode_handler

# Create your tests here
from fecfiler.authentication.models import Account

class SimpleTest(TestCase):
    def setUp(self):
        self.credentials = {
            'username': 'C00601211',
            'password': 'test',
            'email':'test@fec.gov'
        }
        # self.user = Account.objects.create_user(**self.credentials)
        

    def test_login_success(self):
        login_creds = {
            'username': self.credentials.get('username') + self.credentials.get('email'),
            'password': self.credentials.get('password')
        }

        response = self.client.post('/api/v1/user/login/authenticate', login_creds)
        content = json.loads(response.content)
        decoded = jwt_decode_handler(content.get('token'))

        # should be logged in now
        self.assertTrue(content.get('is_allowed'), 'Expected the login result to set is_allowed to true')

        #verify we got a valid token
        self.assertGreater(len(content.get('token')), 50, 'JWT Token returned by login too short')
        self.assertEqual(decoded.get('email'), self.credentials.get('email'), 'JWT email does not match expected email')
