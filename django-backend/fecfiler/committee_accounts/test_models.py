from django.test import TestCase
from .models import CommitteeAccount


class CommitteeAccountTestCase(TestCase):
    fixtures = ["test_committee_accounts"]

    def setUp(self):
        self.valid_committee_account = CommitteeAccount(
            committee_id="C12345678",
        )

    def test_get_contact(self):
        committee_account = CommitteeAccount.objects.get(committee_id="C87654321")
        self.assertEquals(committee_account.committee_id, "C87654321")

    def test_save_and_delete(self):
        self.valid_committee_account.save()
        committee_account_from_db = CommitteeAccount.objects.get(
            committee_id="C12345678"
        )
        self.assertIsInstance(committee_account_from_db, CommitteeAccount)
        self.assertEquals(committee_account_from_db.committee_id, "C12345678")
        committee_account_from_db.delete()
        self.assertRaises(
            CommitteeAccount.DoesNotExist,
            CommitteeAccount.objects.get,
            committee_id="C12345678",
        )

        soft_deleted_committee_account = CommitteeAccount.all_objects.get(
            committee_id="C12345678"
        )
        self.assertEquals(soft_deleted_committee_account.committee_id, "C12345678")
        self.assertIsNotNone(soft_deleted_committee_account.deleted)
        soft_deleted_committee_account.hard_delete()
        self.assertRaises(
            CommitteeAccount.DoesNotExist,
            CommitteeAccount.all_objects.get,
            committee_id="C12345678",
        )
