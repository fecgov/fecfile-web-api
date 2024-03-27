from unittest import mock
from django.test import RequestFactory, TestCase
from rest_framework.test import APIClient

from fecfiler.user.models import User


class UserViewSetTest(TestCase):
    fixtures = ["C01234567_user_and_committee"]

    def setUp(self):
        self.user = User.objects.get(id="12345678-aaaa-bbbb-cccc-111122223333")
        self.factory = RequestFactory()

    @mock.patch("github3.login")
    def test_submit_feedback_happy_path(self, mock_github3):
        
        client = APIClient()
        client.force_authenticate(user=self.user)
        test_headers = {
            "Referer": "test_referer",
            "User-Agent": "test_user_agent"
        }
        test_post_data = {
            "action": "test_action",
            "feedback": "test_feedback",
            "about": "test_about",
        }

        response = client.post("/api/v1/feedback/submit/", data=test_post_data, **test_headers)

        mock_github3.assert_called_once()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {'status': 'feedback submitted'})
