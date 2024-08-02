from django.test import TestCase
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.contacts.models import Contact
from fecfiler.transactions.transaction_dependencies import (
    get_jf_transfer_description,
    update_dependent_descriptions,
)
from fecfiler.transactions.tests.utils import create_schedule_a
from fecfiler.committee_accounts.views import create_committee_view


class TransactionDependenciesTestCase(TestCase):
    def setUp(self):
        self.committee = CommitteeAccount.objects.create(committee_id="C00000000")

        create_committee_view(self.committee.id)
        self.parent_contact = Contact.objects.create(
            committee_account_id=self.committee.id, name="Parent Contact"
        )

    def test_get_jf_transfer_description(self):
        """Test just the logic of generating the description"""
        memo_prefix = "JF Memo:"
        committee_name = "Committee Name"
        is_attribution = False
        expected = "JF Memo: Committee Name"
        self.assertEqual(
            get_jf_transfer_description(memo_prefix, committee_name, is_attribution),
            expected,
        )

        is_attribution = True
        expected = "JF Memo: Committee Name (Partnership Attribution)"
        self.assertEqual(
            get_jf_transfer_description(memo_prefix, committee_name, is_attribution),
            expected,
        )

        memo_prefix = "Pres. Nominating Convention Account JF Memo:"
        is_attribution = True
        committee_name = "Committee Name That Is reeeeeeeeeeeeeeeeeeeeeeaaaaaaaaaaaaaaaaaaaaaaally Long"
        expected = "Pres. Nominating Convention Account JF Memo: Committee Name That Is ree... (Partnership Attribution)"
        self.assertEqual(
            get_jf_transfer_description(memo_prefix, committee_name, is_attribution),
            expected,
        )

    def test_update_dependent_descriptions(self):
        """Test the full process of updating dependent transaction descriptions"""
        parent_transaction = create_schedule_a(
            "JOINT_FUNDRAISING_TRANSFER",
            self.committee,
            self.parent_contact,
            "2020-01-01",
            100,
        )
        child_transaction = create_schedule_a(
            "INDIVIDUAL_JF_TRANSFER_MEMO",
            self.committee,
            self.parent_contact,
            "2020-01-01",
            100,
        )
        grandchild_transaction = create_schedule_a(
            "PARTNERSHIP_ATTRIBUTION_JF_TRANSFER_MEMO",
            self.committee,
            self.parent_contact,
            "2020-01-01",
            100,
        )
        child_transaction.parent_transaction = parent_transaction
        child_transaction.save()
        grandchild_transaction.parent_transaction = child_transaction
        grandchild_transaction.save()
        self.assertIsNone(child_transaction.schedule_a.contribution_purpose_descrip)
        self.assertIsNone(grandchild_transaction.schedule_a.contribution_purpose_descrip)
        update_dependent_descriptions(parent_transaction)
        child_transaction.refresh_from_db()
        grandchild_transaction.refresh_from_db()
        self.assertEquals(
            child_transaction.schedule_a.contribution_purpose_descrip,
            "JF Memo: Parent Contact",
        )
        self.assertEquals(
            grandchild_transaction.schedule_a.contribution_purpose_descrip,
            "JF Memo: Parent Contact (Partnership Attribution)",
        )
