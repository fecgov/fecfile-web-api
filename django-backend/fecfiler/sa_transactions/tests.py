from django.test import TestCase
from .models import SATransaction


class SATransactionTestCase(TestCase):
    """ Test module for inserting a sched_a item"""

    def setUp(self):
        self.sa_trans = SATransaction(
            FORM_TYPE="SA11AI",
            FILER_COMMITTEE_ID_NUMBER="C00123456",
            TRANSACTION_ID="A56123456789-1234",
            ENTITY_TYPE="IND",
            CONTRIBUTOR_ORGANIZATION_NAME="John Smith & Co.",
            CONTRIBUTOR_FIRST_NAME="John",
            CONTRIBUTOR_LAST_NAME="Smith"
        ) 

    def test_save(self):
        self.sa_trans.full_clean()
        self.sa_trans.save()
# Create your tests here.
