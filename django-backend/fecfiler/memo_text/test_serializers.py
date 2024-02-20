from django.test import TestCase
from .serializers import MemoTextSerializer
from fecfiler.user.models import User
from rest_framework.request import Request, HttpRequest


class MemoTextSerializerTestCase(TestCase):
    fixtures = ["test_memo_text", "C01234567_user_and_committee", "test_f3x_reports"]

    def setUp(self):
        self.valid_memo_text = {
            "rec_type": "TEXT",
            "report_id": "b6d60d2d-d926-4e89-ad4b-c47d152a66ae",
            "text4000": "tessst4",
            "transaction_id_number": "REPORT_MEMO_TEXT_3",
            "committee_account": "11111111-2222-3333-4444-555555555555",
        }

        self.invalid_memo_text = {
            "rec_type": "Invalid_rec_type",
            "report_id": "b6d60d2d-d926-4e89-ad4b-c47d152a66ae",
            "text4000": "tessst4",
            "transaction_id_number": "REPORT_MEMO_TEXT_3",
            "committee_account": "11111111-2222-3333-4444-555555555555",
        }

        self.mock_request = Request(HttpRequest())
        self.mock_request.user = User.objects.get(
            id="12345678-aaaa-bbbb-cccc-111122223333"
        )
        self.mock_request.session = {
            "committee_uuid": "11111111-2222-3333-4444-555555555555"
        }

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
