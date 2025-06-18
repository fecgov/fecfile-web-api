from unittest import mock

import github3
from github3 import GitHub
from github3.repos import Repository
from fecfiler.feedback.views import FeedbackViewSet
from fecfiler.shared.viewset_test import FecfilerViewSetTest


class FeedbackViewSetTest(FecfilerViewSetTest):
    fixtures = ["C01234567_user_and_committee"]

    def setUp(self):
        super().setUp()

    @mock.patch.object(github3, "login", return_value=GitHub)
    @mock.patch.object(GitHub, "repository", return_value=Repository)
    @mock.patch.object(Repository, "create_issue")
    def test_submit_feedback_happy_path(
        self, mock_repo_create_issue, mock_github3_repo, mock_github3_login
    ):
        response = self.send_viewset_post_request(
            "/api/v1/feedback/submit/",
            {
                "action": "test_action",
                "feedback": "test_feedback",
                "about": "test_about",
                "location": "<b>test_location</b>",
            },
            FeedbackViewSet,
            "submit_feedback",
            headers={"HTTP_USER_AGENT": "test_user_agent"},
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

    @mock.patch("fecfiler.feedback.views.logger")
    def test_csp_report_happy_path(self, mock_logger):
        test_data = {"type": "csp-violation"}
        response = self.send_viewset_post_request(
            "/api/v1/feedback/csp-report",
            test_data,
            FeedbackViewSet,
            "log_csp_report",
        )
        self.assertEqual(response.status_code, 200)
        mock_logger.warning.assert_called_with({"CSP Failure": test_data})

    @mock.patch("fecfiler.feedback.views.logger")
    def test_csp_report_no_data(self, mock_logger):
        response = self.send_viewset_post_request(
            "/api/v1/feedback/csp-report",
            {},
            FeedbackViewSet,
            "log_csp_report",
        )
        self.assertEqual(response.status_code, 400)
        mock_logger.warning.assert_not_called()

    @mock.patch("fecfiler.feedback.views.logger")
    def test_csp_report_invalid_type(self, mock_logger):
        response = self.send_viewset_post_request(
            "/api/v1/feedback/csp-report",
            {"type": 2},
            FeedbackViewSet,
            "log_csp_report",
        )
        self.assertEqual(response.status_code, 400)
        mock_logger.warning.assert_not_called()
