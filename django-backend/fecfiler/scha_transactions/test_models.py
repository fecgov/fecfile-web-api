from django.test import TestCase
from .models import SchATransaction
from ..reports.f3x_report.models import F3XReport
from ..committee_accounts.models import CommitteeAccount


class SchATransactionTestCase(TestCase):
    fixtures = [
        "test_committee_accounts",
        "test_contacts",
        "test_scha_transactions",
        "test_memo_text",
        "test_f3x_summaries",
    ]

    def setUp(self):
        self.sa_trans = SchATransaction(
            form_type="SA11AI",
            filer_committee_id_number="C00123456",
            entity_type="IND",
            contributor_organization_name="John Smith & Co.",
            contributor_first_name="First",
            contributor_last_name="Last",
            committee_account_id="735db943-9446-462a-9be0-c820baadb622",
        )

    def test_get_scha_transaction(self):
        scha_transaction = SchATransaction.objects.filter(
            contributor_last_name="Smith"
        ).first()
        self.assertEquals(scha_transaction.contributor_first_name, "John")

    def test_get_scha_transaction_in_f3x_summary(self):
        committee = CommitteeAccount()
        f3x = F3XReport(committee_account=committee)
        trans = SchATransaction(committee_account=committee, report=f3x)
        return trans

    def test_parent_related_values(self):
        t1, t2 = SchATransaction.objects.all()[:2]
        t1.parent_transaction = t2
        t1.update_parent_related_values(t2)
        self.assertEqual(t1.back_reference_tran_id_number, t2.transaction_id)
        self.assertEqual(t1.back_reference_sched_name, t2.form_type)

    def test_generate_uid(self):
        committee = CommitteeAccount()
        f3x = F3XReport(committee_account=committee)
        trans = SchATransaction(committee_account=committee, report=f3x)
        self.assertFalse(trans.transaction_id)
        unique_id = trans.generate_unique_transaction_id()
        self.assertTrue(unique_id)
        committee.save()
        f3x.save()
        trans.save()
        saved_trans = SchATransaction.objects.get(id=trans.id)
        self.assertEquals(trans.transaction_id, saved_trans.transaction_id)
        self.assertNotEqual(trans.transaction_id, None)
        self.assertNotEqual(trans.transaction_id, "")
        self.assertEquals(len(trans.transaction_id), 20)

    def test_catches_uid_conflict(self):
        trans = SchATransaction.objects.all()[0]
        existing_uid = trans.transaction_id
        self.assertTrue(SchATransaction.check_for_uid_conflicts(existing_uid))

    def test_save_and_delete(self):
        self.sa_trans.save()
        self.assertEquals(len(self.sa_trans.transaction_id), 20)
        transaction_from_db = SchATransaction.objects.get(contributor_last_name="Last")
        self.assertIsInstance(transaction_from_db, SchATransaction)
        self.assertEquals(transaction_from_db.contributor_first_name, "First")
        transaction_from_db.delete()
        self.assertRaises(
            SchATransaction.DoesNotExist,
            SchATransaction.objects.get,
            contributor_first_name="First",
        )

        soft_deleted_transaction = SchATransaction.all_objects.get(
            contributor_last_name="Last"
        )
        self.assertEquals(soft_deleted_transaction.contributor_first_name, "First")
        self.assertIsNotNone(soft_deleted_transaction.deleted)
        soft_deleted_transaction.hard_delete()
        self.assertRaises(
            SchATransaction.DoesNotExist,
            SchATransaction.all_objects.get,
            contributor_last_name="Last",
        )
