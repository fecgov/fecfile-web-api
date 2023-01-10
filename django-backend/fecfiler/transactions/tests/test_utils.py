from django.test import TestCase
from fecfiler.memo_text.models import MemoText
import uuid

from fecfiler.transactions.utils import get_related_transaction


class UtilsTestCase(TestCase):
    fixtures = [
        "test_committee_accounts",
        "test_f3x_summaries",
        "test_memo_text",
        "test_schedule_a_transaction",
    ]

    def test_get_related_transaction(self):
        memo = MemoText.objects.get(id="a12321aa-a11a-b22b-c33c-abc123321cba")
        transaction = get_related_transaction(memo)
        transaction.id = uuid.UUID("474a1a10-da68-4d71-9a11-9509df48e1aa")
