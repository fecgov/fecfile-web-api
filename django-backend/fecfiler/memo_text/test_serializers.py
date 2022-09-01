from django.test import TestCase
from .serializers import MemoTextSerializer
from fecfiler.authentication.models import Account
from rest_framework.request import Request, HttpRequest


class MemoTextSerializerTestCase(TestCase):
    fixtures = ["test_memo_text", "test_committee_accounts", "test_f3x_summaries"]

    def setUp(self):
        self.valid_memo_text = {
            "back_reference_sched_form_name": "F3XN",
            "filer_committee_id_number": "C00601211",
            "rec_type": "TEXT",
            "report_id": 1,
            "text4000": "tessst4",
            "transaction_id_number": "REPORT_MEMO_TEXT_3",
            "committee_account": 1000,
        }

        self.invalid_memo_text = {
            "back_reference_sched_form_name": "F3XN",
            "filer_committee_id_number": "C00601211",
            "rec_type": "Invalid_rec_type",
            "report_id": 1,
            "text4000": "tessst4",
            "transaction_id_number": "REPORT_MEMO_TEXT_3",
            "committee_account": 1000,
        }

        self.mock_request = Request(HttpRequest())
        user = Account()
        user.cmtee_id = "C00277616"
        self.mock_request.user = user

    def test_serializer_validate(self):
        valid_serializer = MemoTextSerializer(
            data=self.valid_memo_text,
            context={"request": self.mock_request},
        )
        self.assertTrue(valid_serializer.is_valid(raise_exception=True))
        invalid_serializer = MemoTextSerializer(
            data=self.invalid_memo_text,
            context={"request": self.mock_request},
        )
        self.assertFalse(invalid_serializer.is_valid())
        self.assertIsNotNone(invalid_serializer.errors["rec_type"])
