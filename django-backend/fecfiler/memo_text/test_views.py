from django.test import TestCase, RequestFactory
from fecfiler.user.models import User
from rest_framework.test import APIClient
from .views import MemoTextViewSet


class MemoTextViewSetTest(TestCase):
    fixtures = ["test_f3x_reports", "test_memo_text", "C01234567_user_and_committee"]

    def setUp(self):
        self.user = User.objects.get(id="12345678-aaaa-bbbb-cccc-111122223333")
        self.factory = RequestFactory()

    def test_get_memo_texts_for_report_id(self):
        request = self.factory.get(
            "/api/v1/memo-text/?report_id=b6d60d2d-d926-4e89-ad4b-c47d152a66ae"
        )
        request.user = self.user
        request.session = {"committee_uuid": "11111111-2222-3333-4444-555555555555"}
        response = MemoTextViewSet.as_view({"get": "list"})(request)
        self.assertEqual(response.status_code, 200)

    def test_create_new_report_memo_text(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        session = client.session._get_session_from_db()
        session.session_data = client.session.encode(
            {"committee_uuid": "11111111-2222-3333-4444-555555555555"}
        )
        session.save()
        data = {
            "report_id": "1406535e-f99f-42c4-97a8-247904b7d297",
            "rec_type": "TEXT",
            "text4000": "test_new_text",
            "committee_account": "11111111-2222-3333-4444-555555555555",
            "transaction_id_number": "id_number",
            "transaction_uuid": None,
            "fields_to_validate": [
                "report_id",
                "rec_type",
                "text4000",
                "committee_account",
                "transaction_id_number",
                "transaction_uuid",
            ],
        }
        response = client.post("/api/v1/memo-text/", data, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["text4000"], "test_new_text")

    def test_create_existing_report_memo_text(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        session = client.session._get_session_from_db()
        session.session_data = client.session.encode(
            {"committee_uuid": "11111111-2222-3333-4444-555555555555"}
        )
        session.save()
        data = {
            "report_id": "a07c8c65-1b2d-4e6e-bcaa-fa8d39e50965",
            "rec_type": "TEXT",
            "text4000": "test_existing_text",
            "committee_account": "11111111-2222-3333-4444-555555555555",
            "transaction_id_number": "id_number",
            "transaction_uuid": None,
        }
        response = client.post("/api/v1/memo-text/", data, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["text4000"], "test_existing_text")
