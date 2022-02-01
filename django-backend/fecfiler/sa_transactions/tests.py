from django.test import TestCase
from django.core.exceptions import ValidationError
from .models import SATransaction


class SATransactionTestCase(TestCase):
    """ Test module for inserting a sched_a item"""

    def setUp(self):
        self.sa_trans = SATransaction(
            form_type="SA11AI",
            filer_committee_id_number="C00123456",
            transaction_id="A56123456789-1234",
            entity_type="IND",
            contributor_organization_name="John Smith & Co.",
            contributor_first_name="John",
            contributor_last_name="Smith"
        )

        self.bad_trans = SATransaction(
            form_type="SA11AI",
            filer_committee_id_number="C00123456",
            transaction_id="A56123456789-4567",
            entity_type="IND",
            contributor_organization_name="John Smith & Co.",
            contributor_first_name="John",
        )

        self.trans_to_del = SATransaction(
            form_type="SA11AI",
            filer_committee_id_number="C00123456",
            transaction_id="A56123456789-del",
            entity_type="IND",
            contributor_organization_name="John Smith & Co.",
            contributor_first_name="John",
            contributor_last_name="Smith"
        )

    def test_full_clean(self):
        self.sa_trans.full_clean()
        
        self.assertRaises(ValidationError, self.bad_trans.full_clean)

    def test_save(self):
        self.sa_trans.save()
        trans = SATransaction.objects.get(transaction_id="A56123456789-1234")
        self.assertIsInstance(trans, SATransaction)
        self.assertEquals(trans.transaction_id,"A56123456789-1234")

    def test_delete(self):
        self.trans_to_del.save()
        hit = SATransaction.objects.get(transaction_id="A56123456789-del")
        self.assertEquals(hit.transaction_id,"A56123456789-del")
        hit.delete()
        self.assertRaises(SATransaction.DoesNotExist, SATransaction.objects.get,transaction_id="A56123456789-del")
