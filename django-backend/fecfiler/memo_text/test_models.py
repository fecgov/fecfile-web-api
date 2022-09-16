from django.test import TestCase
from .models import MemoText


class MemoTextTestCase(TestCase):
    fixtures = ["test_f3x_summaries", "test_memo_text", "test_committee_accounts"]

    def setUp(self):
        self.valid_memo_text = MemoText(
            back_reference_sched_form_name="F3XN",
            filer_committee_id_number="C00601211",
            id="valid_memo_text",
            rec_type="TEXT",
            text4000="tessst4",
            transaction_id_number="REPORT_MEMO_TEXT_3",
            committee_account_id="735db943-9446-462a-9be0-c820baadb622",
            report_id="b6d60d2d-d926-4e89-ad4b-c47d152a66ae",
        )

    def test_get_memo_text(self):
        memo_text = MemoText.objects.get(id="memo_text_1")
        self.assertEquals(memo_text.text4000, "dahtest2")

    def test_save_and_delete(self):
        self.valid_memo_text.save()
        memo_text_from_db = MemoText.objects.get(id="valid_memo_text")
        self.assertIsInstance(memo_text_from_db, MemoText)
        self.assertEquals(memo_text_from_db.id, "valid_memo_text")
        self.assertEquals(memo_text_from_db.text4000, "tessst4")
