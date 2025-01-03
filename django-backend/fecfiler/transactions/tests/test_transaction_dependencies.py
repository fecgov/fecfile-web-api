from django.test import TestCase
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.contacts.models import Contact
from fecfiler.transactions.transaction_dependencies import (
    get_jf_transfer_descriptions,
    update_dependent_children,
    update_dependent_parent,
)
from fecfiler.transactions.tests.utils import create_schedule_a


class TransactionDependenciesTestCase(TestCase):
    def setUp(self):
        self.committee = CommitteeAccount.objects.create(committee_id="C00000000")
        self.parent_contact = Contact.objects.create(
            committee_account_id=self.committee.id, name="Parent Contact"
        )

    def test_get_jf_transfer_descriptions(self):
        """Test just the logic of generating all the descriptions"""
        memo_prefix = "JF Memo:"
        committee_name = "Committee Name"
        expected = (
            "JF Memo: Committee Name",
            "JF Memo: Committee Name (Partnership Attribution)",
            "JF Memo: Committee Name (Partnership attributions do"
            + " not meet itemization threshold)",
            "JF Memo: Committee Name (See Partnership Attribution(s) below)",
        )
        self.assertEqual(
            get_jf_transfer_descriptions(memo_prefix, committee_name), expected
        )

        memo_prefix = "Pres. Nominating Convention Account JF Memo:"
        committee_name = (
            "Committee Name That Is "
            + "reeeeeeeeeeeeeeeeeeeeeeaaaaaaaaaaaaaaaaaaaaaaally Long"
        )
        expected = (
            "Pres. Nominating Convention Account JF Memo:"
            + " Committee Name That Is"
            + " reeeeeeeeeeeeeeeeeeeeeeaaaaaaaaaaaaaaaaaaaaaaally Long",
            "Pres. Nominating Convention Account JF Memo:"
            + " Committee Name That Is ree... (Partnership Attribution)",
            "Pres. Nominating Convention Account"
            + " ... (Partnership attributions do not meet itemization threshold)",
            "Pres. Nominating Convention Account JF Memo:"
            + " Committee Nam... (See Partnership Attribution(s) below)",
        )
        self.assertEqual(
            get_jf_transfer_descriptions(memo_prefix, committee_name), expected
        )

    def test_jf_memo(self):
        """Test the full process of updating the description for a JF memo"""
        jf_transfer = create_schedule_a(
            "JOINT_FUNDRAISING_TRANSFER",
            self.committee,
            self.parent_contact,
            "2020-01-01",
            100,
        )
        jf_memo = create_schedule_a(
            "INDIVIDUAL_JF_TRANSFER_MEMO",
            self.committee,
            self.parent_contact,
            "2020-01-01",
            100,
        )
        jf_memo.parent_transaction = jf_transfer
        jf_memo.save()
        self.assertIsNone(jf_memo.schedule_a.contribution_purpose_descrip)
        update_dependent_children(jf_transfer)
        jf_memo.refresh_from_db()
        self.assertEquals(
            jf_memo.schedule_a.contribution_purpose_descrip,
            "JF Memo: Parent Contact",
        )

    def test_jf_partnership_memo(self):
        """Test the full process of updating the description for a JF partnership memo"""
        jf_transfer = create_schedule_a(
            "JOINT_FUNDRAISING_TRANSFER",
            self.committee,
            self.parent_contact,
            "2020-01-01",
            100,
        )
        partnership_memo = create_schedule_a(
            "PARTNERSHIP_JF_TRANSFER_MEMO",
            self.committee,
            self.parent_contact,
            "2020-01-01",
            100,
        )
        partnership_memo.parent_transaction = jf_transfer
        partnership_memo.save()
        self.assertIsNone(partnership_memo.schedule_a.contribution_purpose_descrip)
        update_dependent_children(jf_transfer)
        partnership_memo.refresh_from_db()
        self.assertEquals(
            partnership_memo.schedule_a.contribution_purpose_descrip,
            "JF Memo: Parent Contact"
            + " (Partnership attributions do not meet itemization threshold)",
        )

    def test_jf_partnership_memo_with_attribution(self):
        """Test the full process of updating the description
        for a JF partnership memo with an attribution"""
        jf_transfer = create_schedule_a(
            "JOINT_FUNDRAISING_TRANSFER",
            self.committee,
            self.parent_contact,
            "2020-01-01",
            100,
        )
        partnership_memo = create_schedule_a(
            "PARTNERSHIP_JF_TRANSFER_MEMO",
            self.committee,
            self.parent_contact,
            "2020-01-01",
            100,
        )
        partnership_memo.parent_transaction = jf_transfer
        partnership_memo.save()
        attribution_memo = create_schedule_a(
            "PARTNERSHIP_ATTRIBUTION_JF_TRANSFER_MEMO",
            self.committee,
            self.parent_contact,
            "2020-01-01",
            100,
        )
        attribution_memo.parent_transaction = partnership_memo
        attribution_memo.save()
        self.assertIsNone(partnership_memo.schedule_a.contribution_purpose_descrip)
        self.assertIsNone(attribution_memo.schedule_a.contribution_purpose_descrip)
        update_dependent_children(jf_transfer)
        partnership_memo.refresh_from_db()
        attribution_memo.refresh_from_db()
        self.assertEquals(
            partnership_memo.schedule_a.contribution_purpose_descrip,
            "JF Memo: Parent Contact (See Partnership Attribution(s) below)",
        )
        self.assertEquals(
            attribution_memo.schedule_a.contribution_purpose_descrip,
            "JF Memo: Parent Contact (Partnership Attribution)",
        )

    def test_update_dependent_parents(self):
        jf_transfer = create_schedule_a(
            "JOINT_FUNDRAISING_TRANSFER",
            self.committee,
            self.parent_contact,
            "2020-01-01",
            100,
        )
        partnership_memo = create_schedule_a(
            "PARTNERSHIP_JF_TRANSFER_MEMO",
            self.committee,
            self.parent_contact,
            "2020-01-01",
            100,
        )
        partnership_memo.parent_transaction = jf_transfer
        partnership_memo.save()
        attribution_memo = create_schedule_a(
            "PARTNERSHIP_ATTRIBUTION_JF_TRANSFER_MEMO",
            self.committee,
            self.parent_contact,
            "2020-01-01",
            100,
        )
        attribution_memo.parent_transaction = partnership_memo
        attribution_memo.save()
        self.assertIsNone(partnership_memo.schedule_a.contribution_purpose_descrip)
        self.assertIsNone(attribution_memo.schedule_a.contribution_purpose_descrip)
        update_dependent_parent(attribution_memo)
        partnership_memo.refresh_from_db()
        self.assertEquals(
            partnership_memo.schedule_a.contribution_purpose_descrip,
            "JF Memo: Parent Contact (See Partnership Attribution(s) below)",
        )
        attribution_memo.delete()
        update_dependent_parent(attribution_memo)
        partnership_memo.refresh_from_db()
        self.assertEquals(
            partnership_memo.schedule_a.contribution_purpose_descrip,
            "JF Memo: Parent Contact"
            + " (Partnership attributions do not meet itemization threshold)",
        )
