from fecfiler.memo_text.models import MemoText
from ..views import MemoTextViewSet
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.reports.tests.utils import create_form3x
from fecfiler.test.viewset_test import FecfilerViewSetTest


class MemoTextViewSetTest(FecfilerViewSetTest):

    def setUp(self):
        super().setUp()
        self.committee = CommitteeAccount.objects.create(committee_id="C00000000")
        self.q1_report = create_form3x(self.committee, "2024-01-01", "2024-02-01", {})

        MemoText.objects.create(
            rec_type="TEXT",
            is_report_level_memo=True,
            text4000="TEST",
            report_id=self.q1_report.id,
            committee_account_id=self.committee.id,
        )

    def test_get_memo_texts_for_report_id(self):
        response = self.send_viewset_get_request(
            f"/api/v1/memo-text/?report_id={self.q1_report.id}",
            MemoTextViewSet,
            "list",
        )
        self.assertEqual(response.status_code, 200)

    def test_create_new_report_memo_text(self):
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
        response = self.send_viewset_post_request(
            "/api/v1/memo-text/",
            data,
            MemoTextViewSet,
            "create",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["text4000"], "test_new_text")

    def test_create_existing_report_memo_text(self):
        data = {
            "report_id": str(self.q1_report.id),
            "rec_type": "TEXT",
            "text4000": "test_existing_text",
            "committee_account": str(self.committee.id),
            "transaction_id_number": "id_number",
            "transaction_uuid": None,
        }
        response = self.send_viewset_post_request(
            "/api/v1/memo-text/",
            data,
            MemoTextViewSet,
            "create",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["text4000"], "test_existing_text")

        response = self.send_viewset_get_request(
            f"/api/v1/memo-text/?report_id={self.q1_report.id}",
            MemoTextViewSet,
            "list",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_cannot_get_other_committee_memos(self):
        committee2 = CommitteeAccount.objects.create(committee_id="C00000001")
        response = self.send_viewset_get_request(
            f"/api/v1/memo-text/?report_id={self.q1_report.id}",
            MemoTextViewSet,
            "list",
            committee=committee2,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)
