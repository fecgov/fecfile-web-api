from fecfiler.user.models import User
from rest_framework import status
import redis
import threading
import time
from fecfiler.shared.viewset_test import FecfilerViewSetTest
from fecfiler.web_services.models import WebPrintSubmission
from fecfiler.web_services.summary.tasks import CalculationState
from fecfiler.web_services.models import FECStatus
from fecfiler.settings import SYSTEM_STATUS_CACHE_BACKEND
from fecfiler.reports.tests.utils import create_form3x
from fecfiler.committee_accounts.models import CommitteeAccount
from ..views import SSEViewSet
from uuid import uuid4


class SSEViewSetTest(FecfilerViewSetTest):
    def setUp(self):
        self.committee = CommitteeAccount.objects.create(committee_id="C00000000")
        user = User.objects.create(email="test@fec.gov", username="gov")
        super().set_default_user(user)
        super().set_default_committee(self.committee)
        super().setUp()

        self.redis_instance = redis.Redis.from_url(SYSTEM_STATUS_CACHE_BACKEND)
        self.redis_instance.flushdb()

        self.report = create_form3x(
            self.committee,
            "2005-01-01",
            "2005-01-30",
        )
        self.report.calculation_status = CalculationState.CALCULATING
        self.report.save()
        self.completed_report = create_form3x(
            self.committee,
            "2005-01-01",
            "2005-01-30",
        )
        self.completed_report.calculation_status = CalculationState.SUCCEEDED
        self.completed_report.save()

        self.submission = WebPrintSubmission.objects.create(
            fec_status=FECStatus.PROCESSING
        )
        self.completed_submission = WebPrintSubmission.objects.create(
            fec_status=FECStatus.COMPLETED
        )

    def test_unauthenticated_request_fails(self):
        response = self.send_viewset_get_request(
            f"/api/v1/sse/{self.report.id}/calculation-status/",
            SSEViewSet,
            "calculation_status",
            False,
            pk=self.report.id,
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_calculation_status_immediate_return_if_completed(self):
        response = self.send_viewset_get_request(
            f"/api/v1/sse/{self.completed_report.id}/calculation-status/",
            SSEViewSet,
            "calculation_status",
            pk=self.completed_report.id,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = b"".join(response.streaming_content).decode("utf-8")
        self.assertEqual(content, f"data: {CalculationState.SUCCEEDED.value}\n\n")

    def test_calculation_status_report_not_found(self):
        fake_uuid = uuid4()
        response = self.send_viewset_get_request(
            f"/api/v1/sse/{fake_uuid}/calculation-status/",
            SSEViewSet,
            "calculation_status",
            pk=fake_uuid,
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        content = b"".join(response.streaming_content).decode("utf-8")
        self.assertEqual(content, "data: ERROR: Report not found\n\n")

    def test_calculation_status_sse_stream(self):
        def publish_message():
            time.sleep(0.1)
            self.redis_instance.publish(
                f"calculation_status:{self.report.id}", CalculationState.SUCCEEDED.value
            )

        publisher_thread = threading.Thread(target=publish_message)
        publisher_thread.start()

        response = self.send_viewset_get_request(
            f"/api/v1/sse/{self.report.id}/calculation-status/",
            SSEViewSet,
            "calculation_status",
            pk=self.report.id,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        stream_iterator = response.streaming_content

        self.assertEqual(next(stream_iterator).decode("utf-8"), "data: LISTENING\n\n")

        next_message = next(stream_iterator).decode("utf-8")
        if next_message == ": keep-alive\n\n":
            next_message = next(stream_iterator).decode("utf-8")

        self.assertEqual(
            next_message,
            f"data: {CalculationState.SUCCEEDED.value}\n\n",
        )

        with self.assertRaises(StopIteration):
            next(stream_iterator)

        publisher_thread.join()

    def test_webprint_status_immediate_return_if_completed(self):
        response = self.send_viewset_get_request(
            f"/api/v1/sse/{self.completed_submission.id}/webprint-status/",
            SSEViewSet,
            "webprint_status",
            pk=self.completed_submission.id,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = b"".join(response.streaming_content).decode("utf-8")
        self.assertEqual(content, f"data: {FECStatus.COMPLETED.value}\n\n")

    def test_webprint_status_submission_not_found(self):
        fake_uuid = uuid4()
        response = self.send_viewset_get_request(
            f"/api/v1/sse/{fake_uuid}/webprint-status/",
            SSEViewSet,
            "webprint_status",
            pk=fake_uuid,
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        content = b"".join(response.streaming_content).decode("utf-8")
        self.assertEqual(content, "data: ERROR: Submission not found\n\n")

    def test_webprint_status_sse_stream_with_byte_decoding(self):
        def publish_message():
            time.sleep(0.1)
            self.redis_instance.publish(
                f"webprint_status:{self.submission.id}",
                FECStatus.COMPLETED.value.encode("utf-8"),
            )

        publisher_thread = threading.Thread(target=publish_message)
        publisher_thread.start()

        response = self.send_viewset_get_request(
            f"/api/v1/sse/{self.submission.id}/webprint-status/",
            SSEViewSet,
            "webprint_status",
            pk=self.submission.id,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        stream_iterator = response.streaming_content
        self.assertEqual(next(stream_iterator).decode("utf-8"), "data: LISTENING\n\n")

        next_message = next(stream_iterator).decode("utf-8")
        if next_message == ": keep-alive\n\n":
            next_message = next(stream_iterator).decode("utf-8")

        self.assertEqual(
            next_message,
            f"data: {FECStatus.COMPLETED.value}\n\n",
        )

        publisher_thread.join()
