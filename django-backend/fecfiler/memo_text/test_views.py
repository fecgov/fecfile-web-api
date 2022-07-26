from django.test import TestCase, RequestFactory
from ..authentication.models import Account
from rest_framework.test import APIClient


class MemoTextViewSetTest(TestCase):
    fixtures = ["test_memo_text", "test_committee_accounts",
                "test_f3x_summaries", "test_accounts"]

    def setUp(self):
        self.user = Account.objects.get(cmtee_id="C00123456")
        self.factory = RequestFactory()

    def test_create_new_report_memo_text(self):
        client = APIClient()
        client.force_authenticate(user=Account.objects.get(cmtee_id="C00123456"))
        data = {
            "report_id": 3,
            "rec_type": "TEXT",
            "filer_committee_id_number": "C00601211",
            "back_reference_sched_form_name": "F3XN",
            "text4000": "test_new_text",
        }
        response = client.post('/api/v1/memo-text/', data, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['transaction_id_number'],
                         'REPORT_MEMO_TEXT_1')
        self.assertEqual(response.data['text4000'],
                         'test_new_text')

    def test_create_existing_report_memo_text(self):
        client = APIClient()
        client.force_authenticate(user=Account.objects.get(cmtee_id="C00123456"))
        data = {
            "report_id": 2,
            "rec_type": "TEXT",
            "filer_committee_id_number": "C00601211",
            "back_reference_sched_form_name": "F3XN",
            "text4000": "test_existing_text",
        }
        response = client.post('/api/v1/memo-text/', data, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['transaction_id_number'],
                         'REPORT_MEMO_TEXT_3')
        self.assertEqual(response.data['text4000'],
                         'test_existing_text')
