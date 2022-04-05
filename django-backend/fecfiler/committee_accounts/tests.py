from django.test import TestCase
from django.core.exceptions import ValidationError
from .models import CommitteeAccount


class CommitteeAccountTestCase(TestCase):
    def setUp(self):
        self.committee_account = CommitteeAccount(
            committee_id = 'C00601211'
        )

        self.missing_committee_account = CommitteeAccount(
            committee_id = 'C00000000'
        )

        self.committee_account_to_del = CommitteeAccount(
            committee_id = 'C00601211'
        )

    def test_full_clean(self):
        self.sa_trans.full_clean()
        self.assertRaises(ValidationError, self.bad_trans.full_clean)

    def test_save(self):
        self.sa_trans.save()
        trans = SchATransaction.objects.get(transaction_id="A56123456789-1234")
        self.assertIsInstance(trans, SchATransaction)
        self.assertEquals(trans.transaction_id, "A56123456789-1234")

    def test_delete(self):
        self.trans_to_del.save()
        hit = SchATransaction.objects.get(transaction_id="A56123456789-del")
        self.assertEquals(hit.transaction_id, "A56123456789-del")
        hit.delete()
        self.assertRaises(
            SchATransaction.DoesNotExist,
            SchATransaction.objects.get,
            transaction_id="A56123456789-del",
        )

        soft_deleted_transaction = SchATransaction.all_objects.get(
            transaction_id="A56123456789-del"
        )
        self.assertIsNotNone(soft_deleted_transaction.deleted)
        soft_deleted_transaction.hard_delete()
        self.assertRaises(
            SchATransaction.DoesNotExist,
            SchATransaction.all_objects.get,
            transaction_id="A56123456789-del",
        )
