from unittest import mock

import github3
from django.test import RequestFactory, TestCase
from fecfiler.user.models import User
from github3 import GitHub
from github3.repos import Repository
from rest_framework.test import APIClient


class UserViewSetTest(TestCase):
    fixtures = ["C01234567_user_and_committee"]

    def setUp(self):
        self.user = User.objects.get(id="12345678-aaaa-bbbb-cccc-111122223333")
        self.factory = RequestFactory()

    @mock.patch.object(github3, "login", return_value=GitHub)
    @mock.patch.object(GitHub, "repository", return_value=Repository)
    @mock.patch.object(Repository, "create_issue")
    def test_submit_feedback_happy_path(
        self, mock_repo_create_issue, mock_github3_repo, mock_github3_login
    ):
        client = APIClient()
        client.force_authenticate(user=self.user)
        test_headers = {"HTTP_USER_AGENT": "test_user_agent"}
        test_post_data = {
            "action": "test_action",
            "feedback": "test_feedback",
            "about": "test_about",
            "location": "<b>test_location</b>",
        }

        response = client.post(
            "/api/v1/feedback/submit/", data=test_post_data, **test_headers
        )

        mock_github3_login.assert_called_once()
        mock_github3_repo.assert_called_once()
        mock_repo_create_issue.assert_called_once()
        title, body = mock_repo_create_issue.call_args
        body_content = body["body"]
        self.assertEqual("User feedback on &lt;b&gt;test_location&lt;/b&gt;", title[0])
        self.assertTrue("test_action" in body_content)
        self.assertTrue("test_feedback" in body_content)
        self.assertTrue("test_about" in body_content)
        self.assertTrue("&lt;b&gt;test_location&lt;/b&gt;" in body_content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"status": "feedback submitted"})
