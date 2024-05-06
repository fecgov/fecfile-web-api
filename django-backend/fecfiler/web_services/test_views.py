from datetime import datetime
import math
from unittest.mock import patch
from uuid import UUID
from django.test import TestCase, RequestFactory
from fecfiler.web_services.views import WebServicesViewSet
from rest_framework.test import force_authenticate
from fecfiler.user.models import User
import structlog

logger = structlog.get_logger(__name__)


class WebServicesViewSetTest(TestCase):
    fixtures = [
        "C01234567_user_and_committee",
        "test_f3x_reports",
    ]

    def setUp(self):
        self.factory = RequestFactory()
        self.task_id = "testTaskId"
        self.view = WebServicesViewSet()
        self.user = User.objects.get(id="12345678-aaaa-bbbb-cccc-111122223333")

    @patch("fecfiler.web_services.views.AsyncResult")
    def test_check_dot_fec_ready(self, mock_async_result):
        request = self.factory.get(f"api/v1/web-services/dot-fec/check/{self.task_id}")
        mock_instance = mock_async_result.return_value
        mock_instance.ready.return_value = True
        mock_instance.get.return_value = "testId"
        self.view.request = request
        response = self.view.check_dot_fec(request, self.task_id)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"done": True, "id": "testId"})

    @patch("fecfiler.web_services.views.AsyncResult")
    def test_check_dot_fec_not_ready(self, mock_async_result):
        request = self.factory.get(f"api/v1/web-services/dot-fec/check/{self.task_id}")
        mock_instance = mock_async_result.return_value
        mock_instance.ready.return_value = False
        mock_instance.get.return_value = "testId"
        self.view.request = request
        response = self.view.check_dot_fec(request, self.task_id)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"done": False})

    @patch("fecfiler.web_services.views.create_dot_fec.apply_async")
    def test_create_dot_fec(self, mock_apply_async):
        mock_instance = mock_apply_async.return_value
        mock_instance.task_id = "testTaskId"

        data = {
            "report_id": "b6d60d2d-d926-4e89-ad4b-c47d152a66ae",
        }
        request = self.factory.post(
            "api/v1/web-services/dot-fec/", data, "application/json"
        )
        request.data = data
        request.user = self.user
        request.session = {
            "committee_uuid": "11111111-2222-3333-4444-555555555555",
            "committee_id": "C01234567",
        }
        force_authenticate(request, user=self.user)
        response = self.view.create_dot_fec(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data,
            {
                "file_name": (
                    f"{data['report_id']}_{math.floor(datetime.now().timestamp())}.fec"
                ),
                "task_id": mock_instance.task_id,
            },
        )

    def test_get_dot_fec_not_exists(self):
        id = "b6d60d2d-d926-4e89-ad4b-c47d152a66ae"

        request = self.factory.get(f"api/v1/web-services/dot-fec/{id}")
        request.session = {
            "committee_uuid": UUID("11111111-2222-3333-4444-555555555555"),
            "committee_id": "C01234567",
        }
        force_authenticate(request, user=self.user)
        response = self.view.get_dot_fec(request, id)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, f"No .FEC was found for id: {id}")
