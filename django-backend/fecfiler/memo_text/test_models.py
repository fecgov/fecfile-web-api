from django.test import TestCase
from .models import MemoText


class MemoTextTestCase(TestCase):
    fixtures = ["test_memo_text"]

    def setUp(self):
        self.valid_memo_text = MemoText(
            back_reference_sched_form_name="F3XN",
            filer_committee_id_number="C00601211",
            id=30,
            rec_type="TEXT",
            text4000="tessst4",
            transaction_id_number="REPORT_MEMO_TEXT_3"
        )

    def test_get_memo_text(self):
        memo_text = MemoText.objects.get(id=25)
        self.assertEquals(memo_text.text4000, "dahtest2")

    def test_save_and_delete(self):
        self.valid_memo_text.save()
        memo_text_from_db = MemoText.objects.get(
            id=30
        )
        self.assertIsInstance(memo_text_from_db, MemoText)
        self.assertEquals(memo_text_from_db.id, 30)
        self.assertEquals(memo_text_from_db.text4000, "tessst4")
