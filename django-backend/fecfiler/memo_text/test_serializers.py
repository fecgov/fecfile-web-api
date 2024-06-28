from django.test import TestCase
from .serializers import MemoTextSerializer
from fecfiler.user.models import User
from rest_framework.request import Request, HttpRequest
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.committee_accounts.views import create_committee_view
from fecfiler.reports.tests.utils import create_form3x


class MemoTextSerializerTestCase(TestCase):

    def setUp(self):
        self.committee = CommitteeAccount.objects.create(committee_id="C00000000")
        self.user = User.objects.create(email="test@fec.gov", username="gov")
        create_committee_view(self.committee.id)
        q1_report = create_form3x(self.committee, "2024-01-01", "2024-02-01", {})

        self.valid_memo_text = {
            "rec_type": "TEXT",
            "report_id": q1_report.id,
            "text4000": "tessst4",
            "transaction_id_number": "REPORT_MEMO_TEXT_3",
            "committee_account": self.committee.id,
        }

        self.invalid_memo_text = {
            "rec_type": "Invalid_rec_type",
            "report_id": q1_report.id,
            "text4000": "tessst4",
            "transaction_id_number": "REPORT_MEMO_TEXT_3",
            "committee_account": self.committee.id,
        }

        self.mock_request = Request(HttpRequest())
        self.mock_request.user = self.user
        self.mock_request.session = {
            "committee_uuid": str(self.committee.id),
            "committee_id": str(self.committee.committee_id),
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
