import unittest
from unittest.mock import Mock


from django.test import RequestFactory

from fecfiler.authentication.token import (login_dot_gov_logout,
                                           generate_username)


class TestToken(unittest.TestCase):

    def setUp(self):
        self.factory = RequestFactory()

    def test_login_dot_gov_logout_happy_path(self):
        test_state = 'test_state'

        mock_request = Mock()
        mock_request.session = Mock()
        mock_request.get_signed_cookie.return_value = test_state

        retval = login_dot_gov_logout(mock_request)
        self.maxDiff = None
        self.assertEqual(retval, ('https://idp.int.identitysandbox.gov'
                                  '/openid_connect/logout?'
                                  'client_id=None'
                                  '&post_logout_redirect_uri=None'
                                  '&state=test_state'))

    def test_generate_username(self):
        test_uuid = 'test_uuid'
        retval = generate_username(test_uuid)
        self.assertEqual(test_uuid, retval)
