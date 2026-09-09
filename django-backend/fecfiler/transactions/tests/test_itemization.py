from decimal import Decimal
from django.test import TestCase
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.contacts.tests.utils import create_test_individual_contact
from fecfiler.transactions.itemization import (
    calculate_itemization,
    cascade_itemization_to_parents,
    cascade_unitemization_to_children,
    get_all_children_ids,
    get_all_parent_ids,
    has_itemized_children,
)
from fecfiler.transactions.tests.utils import create_schedule_a


class TransactionItemizationTestCase(TestCase):
    def setUp(self):
        self.committee = CommitteeAccount.objects.create(committee_id="C00000000")
        self.contact = create_test_individual_contact(
            "last name", "first name", self.committee.id
        )

    def test_calculate_itemization_respects_force_itemized_override(self):
        transaction = create_schedule_a(
            "INDIVIDUAL_RECEIPT",
            self.committee,
            self.contact,
            "2024-01-01",
            "50.00",
        )

        transaction.force_itemized = True
        self.assertTrue(calculate_itemization(transaction))

        transaction.force_itemized = False
        self.assertFalse(calculate_itemization(transaction))

    def test_calculate_itemization_uses_itemized_children_under_threshold(self):
        parent = create_schedule_a(
            "INDIVIDUAL_RECEIPT",
            self.committee,
            self.contact,
            "2024-01-01",
            "50.00",
        )
        child = create_schedule_a(
            "PARTNERSHIP_ATTRIBUTION",
            self.committee,
            self.contact,
            "2024-01-02",
            "20.00",
            parent_id=parent.id,
        )
        child.itemized = True
        child.save(update_fields=["itemized"])

        self.assertTrue(has_itemized_children(parent))
        self.assertTrue(calculate_itemization(parent))

    def test_get_all_children_ids_and_parent_ids_recursive(self):
        root = create_schedule_a(
            "PARTNERSHIP_RECEIPT",
            self.committee,
            self.contact,
            "2024-01-01",
            "100.00",
        )
        child = create_schedule_a(
            "PARTNERSHIP_ATTRIBUTION",
            self.committee,
            self.contact,
            "2024-01-02",
            "30.00",
            parent_id=root.id,
        )
        grandchild = create_schedule_a(
            "PARTNERSHIP_ATTRIBUTION",
            self.committee,
            self.contact,
            "2024-01-03",
            "20.00",
            parent_id=child.id,
        )

        self.assertEqual(set(get_all_children_ids(root.id)), {child.id, grandchild.id})
        self.assertEqual(set(get_all_parent_ids(grandchild)), {root.id, child.id})

    def test_cascade_itemization_to_parents_sets_itemized_and_clears_force_flag(self):
        root = create_schedule_a(
            "INDIVIDUAL_RECEIPT",
            self.committee,
            self.contact,
            "2024-01-01",
            "50.00",
            itemized=False,
        )
        child = create_schedule_a(
            "PARTNERSHIP_ATTRIBUTION",
            self.committee,
            self.contact,
            "2024-01-02",
            "25.00",
            parent_id=root.id,
            itemized=False,
        )
        grandchild = create_schedule_a(
            "PARTNERSHIP_ATTRIBUTION",
            self.committee,
            self.contact,
            "2024-01-03",
            "25.00",
            parent_id=child.id,
            itemized=False,
        )

        root.force_itemized = False
        child.force_itemized = False
        root.save(update_fields=["force_itemized"])
        child.save(update_fields=["force_itemized"])

        grandchild.itemized = True
        grandchild.save(update_fields=["itemized"])

        cascade_itemization_to_parents(grandchild)

        root.refresh_from_db()
        child.refresh_from_db()

        self.assertTrue(root.itemized)
        self.assertTrue(child.itemized)
        self.assertIsNone(root.force_itemized)
        self.assertIsNone(child.force_itemized)

    def test_cascade_unitemization_to_children_sets_descendants_unitemized(self):
        root = create_schedule_a(
            "INDIVIDUAL_RECEIPT",
            self.committee,
            self.contact,
            "2024-01-01",
            "300.00",
        )
        child = create_schedule_a(
            "PARTNERSHIP_ATTRIBUTION",
            self.committee,
            self.contact,
            "2024-01-02",
            "40.00",
            parent_id=root.id,
        )
        grandchild = create_schedule_a(
            "PARTNERSHIP_ATTRIBUTION",
            self.committee,
            self.contact,
            "2024-01-03",
            "25.00",
            parent_id=child.id,
        )

        root.itemized = False
        root.save(update_fields=["itemized"])

        cascade_unitemization_to_children(root)

        child.refresh_from_db()
        grandchild.refresh_from_db()

        self.assertFalse(child.itemized)
        self.assertFalse(grandchild.itemized)

    def test_calculate_itemization_with_negative_aggregate_is_itemized(self):
        transaction = create_schedule_a(
            "INDIVIDUAL_RECEIPT",
            self.committee,
            self.contact,
            "2024-01-01",
            "50.00",
        )
        transaction.aggregate = Decimal("-1.00")
        transaction.force_itemized = None

        self.assertTrue(calculate_itemization(transaction))
