from django.test import TestCase, RequestFactory
from ..authentication.models import Account
from rest_framework.test import APIClient
from .views import MemoTextViewSet


class MemoTextViewSetTest(TestCase):
    fixtures = [
        "test_f3x_summaries",
        "test_memo_text",
        "test_committee_accounts",
        "test_accounts",
    ]

    def setUp(self):
        self.user = Account.objects.get(cmtee_id="C12345678")
        self.factory = RequestFactory()

    def test_get_memo_texts_for_report_id(self):
        request = self.factory.get("/api/v1/memo-text/?report_id=9999")
        request.user = self.user
        response = MemoTextViewSet.as_view({"get": "list"})(request)
        self.assertEqual(response.status_code, 200)

    def test_create_new_report_memo_text(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        data = {
            "report_id": 10001,
            "rec_type": "TEXT",
            "filer_committee_id_number": "C00601211",
            "back_reference_sched_form_name": "F3XN",
            "text4000": "test_new_text",
        }
        response = client.post("/api/v1/memo-text/", data, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["transaction_id_number"], "REPORT_MEMO_TEXT_1")
        self.assertEqual(response.data["text4000"], "test_new_text")

    def test_create_existing_report_memo_text(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        data = {
            "report_id": 10000,
            "rec_type": "TEXT",
            "filer_committee_id_number": "C00601211",
            "back_reference_sched_form_name": "F3XN",
            "text4000": "test_existing_text",
        }
        response = client.post("/api/v1/memo-text/", data, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["transaction_id_number"], "REPORT_MEMO_TEXT_3")
        self.assertEqual(response.data["text4000"], "test_existing_text")
