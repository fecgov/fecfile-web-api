from django.test import TestCase
from .serializers import MemoTextSerializer
from fecfiler.authentication.models import Account
from rest_framework.request import Request, HttpRequest


class MemoTextSerializerTestCase(TestCase):
    fixtures = ["test_memo_text", "test_committee_accounts", "test_f3x_summaries"]

    def setUp(self):
        self.valid_memo_text = {
            "back_reference_sched_form_name": "F3XN",
            "rec_type": "TEXT",
            "report_id": "b6d60d2d-d926-4e89-ad4b-c47d152a66ae",
            "text4000": "tessst4",
            "transaction_id_number": "REPORT_MEMO_TEXT_3",
            "committee_account": "735db943-9446-462a-9be0-c820baadb622",
        }

        self.invalid_memo_text = {
            "back_reference_sched_form_name": "F3XN",
            "rec_type": "Invalid_rec_type",
            "report_id": "b6d60d2d-d926-4e89-ad4b-c47d152a66ae",
            "text4000": "tessst4",
            "transaction_id_number": "REPORT_MEMO_TEXT_3",
            "committee_account": "735db943-9446-462a-9be0-c820baadb622",
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
