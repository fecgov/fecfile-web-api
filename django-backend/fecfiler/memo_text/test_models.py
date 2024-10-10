import uuid
from django.test import TestCase
from .models import MemoText
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.committee_accounts.utils import create_committee_view
from fecfiler.reports.tests.utils import create_form3x


class MemoTextTestCase(TestCase):

    def setUp(self):
        self.committee = CommitteeAccount.objects.create(committee_id="C00000000")
        create_committee_view(self.committee.id)
        q1_report = create_form3x(self.committee, "2024-01-01", "2024-02-01", {})

        self.valid_memo_text = MemoText(
            id="94777fb3-6d3a-4e2c-87dc-5e6ed326e65b",
            rec_type="TEXT",
            text4000="tessst4",
            committee_account_id=self.committee.id,
            report_id=q1_report.id,
        )

    def test_get_memo_text(self):
        self.valid_memo_text.save()
        memo_text = MemoText.objects.get(id="94777fb3-6d3a-4e2c-87dc-5e6ed326e65b")
        self.assertEquals(memo_text.text4000, "tessst4")

    def test_save_and_delete(self):
        self.valid_memo_text.save()
        memo_text_from_db = MemoText.objects.get(
            id="94777fb3-6d3a-4e2c-87dc-5e6ed326e65b"
        )
        self.assertIsInstance(memo_text_from_db, MemoText)
        self.assertEquals(
            memo_text_from_db.id, uuid.UUID("94777fb3-6d3a-4e2c-87dc-5e6ed326e65b")
        )
        self.assertEquals(memo_text_from_db.transaction_id_number, "REPORT_MEMO_TEXT1")
        self.assertEquals(memo_text_from_db.text4000, "tessst4")
