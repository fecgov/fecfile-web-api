from django.test import TestCase, RequestFactory
from fecfiler.user.models import User
from fecfiler.memo_text.models import MemoText
from rest_framework.test import APIClient
from .views import MemoTextViewSet
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.reports.tests.utils import create_form3x


class MemoTextViewSetTest(TestCase):

    def setUp(self):
        self.committee = CommitteeAccount.objects.create(committee_id="C00000000")
        self.user = User.objects.create(email="test@fec.gov", username="gov")
        self.q1_report = create_form3x(self.committee, "2024-01-01", "2024-02-01", {})
        self.factory = RequestFactory()

        MemoText.objects.create(
            rec_type="TEXT",
            is_report_level_memo=True,
            text4000="TEST",
            report_id=self.q1_report.id,
            committee_account_id=self.committee.id,
        )

    def test_get_memo_texts_for_report_id(self):
        request = self.factory.get(f"/api/v1/memo-text/?report_id={self.q1_report.id}")
        request.user = self.user
        request.session = {
            "committee_uuid": str(self.committee.id),
            "committee_id": str(self.committee.committee_id),
        }
        response = MemoTextViewSet.as_view({"get": "list"})(request)
        self.assertEqual(response.status_code, 200)

    def test_create_new_report_memo_text(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        session = client.session._get_session_from_db()
        session.session_data = client.session.encode(
            {"committee_uuid": str(self.committee.id)}
        )
        session.save()
        data = {
            "report_id": self.q1_report.id,
            "rec_type": "TEXT",
            "text4000": "test_new_text",
            "committee_account": str(self.committee.id),
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
        response = client.post("/api/v1/memo-text/", data, format="json", secure=True)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["text4000"], "test_new_text")

    def test_create_existing_report_memo_text(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        session = client.session._get_session_from_db()
        session.session_data = client.session.encode(
            {"committee_uuid": str(self.committee.id)}
        )
        session.save()
        data = {
            "report_id": str(self.q1_report.id),
            "rec_type": "TEXT",
            "text4000": "test_existing_text",
            "committee_account": str(self.committee.id),
            "transaction_id_number": "id_number",
            "transaction_uuid": None,
        }
        response = client.post("/api/v1/memo-text/", data, format="json", secure=True)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["text4000"], "test_existing_text")

    def test_can_get_own_committee_memos(self):
        request = self.factory.get(f"/api/v1/memo-text/?report_id={self.q1_report.id}")
        request.user = self.user
        request.session = {
            "committee_uuid": str(self.committee.id),
            "committee_id": str(self.committee.committee_id),
        }

        response = MemoTextViewSet.as_view({"get": "list"})(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_cannot_get_other_committee_memos(self):
        committee2 = CommitteeAccount.objects.create(committee_id="C00000001")
        request = self.factory.get(f"/api/v1/memo-text/?report_id={self.q1_report.id}")
        request.user = self.user
        request.session = {
            "committee_uuid": str(committee2.id),
            "committee_id": str(committee2.committee_id),
        }

        response = MemoTextViewSet.as_view({"get": "list"})(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)
