import uuid
from django.test import TestCase
from .models import MemoText


class MemoTextTestCase(TestCase):
    fixtures = ["test_f3x_summaries", "test_memo_text", "test_committee_accounts"]

    def setUp(self):
        self.valid_memo_text = MemoText(
            id="94777fb3-6d3a-4e2c-87dc-5e6ed326e65b",
            rec_type="TEXT",
            text4000="tessst4",
            committee_account_id="735db943-9446-462a-9be0-c820baadb622",
            report_id="b6d60d2d-d926-4e89-ad4b-c47d152a66ae",
        )

    def test_get_memo_text(self):
        memo_text = MemoText.objects.get(id="1dee28f8-4cfa-4f70-8658-7a9e7f02ab1d")
        self.assertEquals(memo_text.text4000, "dahtest2")

    def test_save_and_delete(self):
        self.valid_memo_text.save()
        memo_text_from_db = MemoText.objects.get(
            id="94777fb3-6d3a-4e2c-87dc-5e6ed326e65b"
        )
        self.assertIsInstance(memo_text_from_db, MemoText)
        self.assertEquals(
            memo_text_from_db.id, uuid.UUID("94777fb3-6d3a-4e2c-87dc-5e6ed326e65b")
        )
        self.assertEquals(memo_text_from_db.transaction_id_number, "REPORT_MEMO_TEXT2")
        self.assertEquals(memo_text_from_db.text4000, "tessst4")
