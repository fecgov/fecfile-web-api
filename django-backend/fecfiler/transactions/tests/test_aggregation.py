from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import TestCase

from fecfiler.transactions.aggregation import (
    process_aggregation_by_payee_candidate,
    process_aggregation_for_debts,
    process_aggregation_for_election,
    process_aggregation_for_entity,
    reaggregate_after_report_deletion,
    schedule_a_over_two_hundred_types,
)
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.contacts.models import Contact, ContactType
from fecfiler.election_cycles.models import ElectionCycle
from fecfiler.transactions.models import Transaction
from fecfiler.transactions.schedule_a.models import ScheduleA


class AggregationDirectFunctionTestCase(TestCase):
    @patch("fecfiler.transactions.aggregation.ScheduleD.objects.bulk_update")
    @patch("fecfiler.transactions.aggregation.Transaction.objects.filter")
    def test_process_aggregation_for_debts_returns_when_transaction_missing(
        self, filter_mock, bulk_update_mock
    ):
        first_qs = MagicMock()
        id_qs = MagicMock()
        id_qs.first.return_value = None
        first_qs.filter.return_value = id_qs
        filter_mock.return_value = first_qs

        process_aggregation_for_debts(MagicMock(id="txn-1", committee_account_id="c-1"))

        bulk_update_mock.assert_not_called()

    @patch("fecfiler.transactions.aggregation.ScheduleD.objects.bulk_update")
    @patch("fecfiler.transactions.aggregation.Transaction.objects.filter")
    def test_process_aggregation_for_debts_returns_when_given_debt_missing(
        self, filter_mock, bulk_update_mock
    ):
        transaction = MagicMock()
        transaction.schedule_d = None
        transaction.debt = None

        first_qs = MagicMock()
        id_qs = MagicMock()
        id_qs.first.return_value = transaction
        first_qs.filter.return_value = id_qs
        filter_mock.return_value = first_qs

        process_aggregation_for_debts(MagicMock(id="txn-2", committee_account_id="c-1"))

        bulk_update_mock.assert_not_called()

    @patch("fecfiler.transactions.aggregation.ScheduleF.objects.bulk_update")
    @patch(
        "fecfiler.transactions.aggregation."
        "filter_queryset_for_previous_transactions_in_aggregation"
    )
    @patch("fecfiler.transactions.aggregation.Transaction.objects.filter")
    def test_process_aggregation_by_payee_candidate_recalculates_from_earliest_date(
        self,
        filter_mock,
        previous_filter_mock,
        bulk_update_mock,
    ):
        instance = MagicMock(id="txn-1", committee_account_id="committee-1")

        current_transaction = MagicMock()
        current_transaction.id = "txn-1"
        current_transaction.date = date(2024, 2, 1)
        current_transaction.created = datetime(2024, 2, 1, 12, 0, 0)
        current_transaction.contact_2 = "contact-2"
        current_transaction.contact_2_id = "contact-2"
        current_transaction.aggregation_group = "GENERAL"
        current_transaction.schedule_f = MagicMock(general_election_year="2024")

        older_trans = MagicMock()
        older_trans.schedule_f = MagicMock(expenditure_amount=Decimal("10.00"))
        newer_trans = MagicMock()
        newer_trans.schedule_f = MagicMock(expenditure_amount=Decimal("20.00"))

        id_qs = MagicMock()
        id_qs.first.return_value = current_transaction

        committee_qs = MagicMock()
        shared_entity_qs = MagicMock()
        affected_qs = MagicMock()

        committee_qs.filter.return_value = shared_entity_qs
        shared_entity_qs.filter.return_value = affected_qs
        affected_qs.order_by.return_value = [older_trans, newer_trans]

        def filter_side_effect(*args, **kwargs):
            if kwargs == {"id": "txn-1"}:
                return id_qs
            if kwargs == {"committee_account_id": "committee-1"}:
                return committee_qs
            raise AssertionError(f"Unexpected filter call: {kwargs}")

        filter_mock.side_effect = filter_side_effect

        previous_qs = MagicMock()
        previous_qs.first.return_value = MagicMock(
            schedule_f=MagicMock(aggregate_general_elec_expended=Decimal("99.00"))
        )
        previous_filter_mock.return_value = previous_qs

        process_aggregation_by_payee_candidate(
            instance,
            old_snapshot={"date": date(2024, 1, 15)},
        )

        shared_entity_qs.filter.assert_called_once_with(date__gte=date(2024, 1, 15))
        self.assertEqual(
            older_trans.schedule_f.aggregate_general_elec_expended,
            Decimal("10.00"),
        )
        self.assertEqual(
            newer_trans.schedule_f.aggregate_general_elec_expended,
            Decimal("30.00"),
        )
        bulk_update_mock.assert_called_once()

    @patch("fecfiler.transactions.aggregation.Transaction.objects.bulk_update")
    @patch("fecfiler.transactions.aggregation.Transaction.objects.filter")
    def test_process_aggregation_for_election_uses_null_state_filter(
        self, filter_mock, bulk_update_mock
    ):
        trans = MagicMock()
        trans.schedule_e = MagicMock(election_code="H2024")
        trans.contact_2 = MagicMock(
            candidate_office="H",
            candidate_state=None,
            candidate_district="01",
        )
        trans.committee_account_id = "committee-1"
        trans.aggregation_group = "INDEPENDENT_EXPENDITURE"
        trans.get_date.return_value = date(2024, 2, 1)

        first = MagicMock()
        first.election_agg = Decimal("5.00")
        annotated_qs = MagicMock()
        ordered_qs = MagicMock()
        filter_mock.return_value = annotated_qs
        annotated_qs.order_by.return_value = ordered_qs
        ordered_qs.annotate.return_value = [first]

        process_aggregation_for_election(trans)

        filter_kwargs = filter_mock.call_args.kwargs
        self.assertTrue(filter_kwargs["contact_2__candidate_state__isnull"])
        self.assertEqual(filter_kwargs["contact_2__candidate_district"], "01")
        self.assertEqual(first._calendar_ytd_per_election_office, Decimal("5.00"))
        bulk_update_mock.assert_called_once()

    @patch("fecfiler.transactions.aggregation.process_aggregation_for_entity_contact")
    def test_process_aggregation_for_entity_delegates(self, delegate_mock):
        transaction = MagicMock(
            committee_account_id="committee-1",
            aggregation_group="GENERAL",
            contact_1_id="contact-1",
        )

        process_aggregation_for_entity(transaction, earliest_date=date(2024, 3, 1))

        delegate_mock.assert_called_once_with(
            "committee-1",
            "GENERAL",
            "contact-1",
            date(2024, 3, 1),
        )

    @patch("fecfiler.transactions.aggregation.process_aggregation_for_entity_contact")
    @patch("fecfiler.transactions.aggregation.Transaction.objects.filter")
    def test_reaggregate_after_report_deletion_filters_contexts(
        self,
        filter_mock,
        entity_contact_mock,
    ):
        include_type = schedule_a_over_two_hundred_types[0]

        included = MagicMock(
            transaction_type_identifier=include_type,
            contact_1_id="contact-1",
            committee_account_id="committee-1",
            aggregation_group="GENERAL",
        )
        excluded_type = MagicMock(
            transaction_type_identifier="LOAN_BY_COMMITTEE",
            contact_1_id="contact-2",
            committee_account_id="committee-1",
            aggregation_group="GENERAL",
        )
        excluded_no_contact = MagicMock(
            transaction_type_identifier=include_type,
            contact_1_id=None,
            committee_account_id="committee-1",
            aggregation_group="GENERAL",
        )

        filter_mock.return_value = [included, excluded_type, excluded_no_contact]

        callback = reaggregate_after_report_deletion(MagicMock(id="r-1"))
        callback()

        entity_contact_mock.assert_called_once_with(
            "committee-1",
            "GENERAL",
            "contact-1",
        )

    @patch("fecfiler.transactions.aggregation.ScheduleF.objects.bulk_update")
    @patch("fecfiler.transactions.aggregation.Transaction.objects.filter")
    def test_process_aggregation_by_payee_candidate_returns_when_no_aggregation_group(
        self, filter_mock, bulk_update_mock
    ):
        transaction = MagicMock()
        transaction.aggregation_group = None

        id_qs = MagicMock()
        id_qs.first.return_value = transaction
        filter_mock.return_value = id_qs

        instance = MagicMock(id="txn-null-group", committee_account_id="committee-1")
        process_aggregation_by_payee_candidate(instance)

        bulk_update_mock.assert_not_called()

    @patch("fecfiler.transactions.aggregation.Transaction.objects.filter")
    def test_process_aggregation_for_entity_contact_returns_when_no_aggregation_group(
        self, filter_mock
    ):
        from fecfiler.transactions.aggregation import (
            process_aggregation_for_entity_contact,
        )

        process_aggregation_for_entity_contact(
            committee_account_id="committee-1",
            aggregation_group=None,
            contact_1_id="contact-1",
        )
        filter_mock.assert_not_called()

    @patch("fecfiler.transactions.aggregation.process_aggregation_for_entity_contact")
    def test_process_aggregation_for_entity_returns_when_no_aggregation_group(
        self, delegate_mock
    ):
        transaction = MagicMock(
            committee_account_id="committee-1",
            aggregation_group=None,
            contact_1_id="contact-1",
        )

        process_aggregation_for_entity(transaction)
        delegate_mock.assert_not_called()

    @patch("fecfiler.transactions.aggregation.Transaction.objects.filter")
    def test_process_aggregation_for_election_returns_when_aggregation_group_missing(
        self, filter_mock
    ):
        trans = MagicMock()
        trans.aggregation_group = None
        trans.schedule_e = MagicMock(election_code="H2024")
        trans.contact_2 = MagicMock(candidate_office="H")

        process_aggregation_for_election(trans)
        filter_mock.assert_not_called()

    @patch(
        "fecfiler.transactions.aggregation.process_aggregation_for_entity_election_cycle"
    )
    def test_update_election_cycle_aggregates_for_transaction(self, delegate_mock):
        test_committee = CommitteeAccount.objects.create(committee_id="C00000003")
        test_contact_1 = Contact.objects.create(
            type=ContactType.INDIVIDUAL,
            last_name="test_last_name",
            first_name="test_first_name",
            committee_account_id=test_committee.id,
        )
        test_election_cycle_1_start_date = "2023-01-01"
        test_election_cycle_1_end_date = "2024-12-31"
        ElectionCycle.objects.create(
            committee_account=test_committee,
            office=ElectionCycle.Office.SENATE,
            election_type=ElectionCycle.ElectionType.GENERAL,
            election_year="2026",
            start_date=test_election_cycle_1_start_date,
            end_date=test_election_cycle_1_end_date,
        )
        test_election_cycle_2_start_date = "2025-01-01"
        test_election_cycle_2_end_date = "2026-12-31"
        ElectionCycle.objects.create(
            committee_account=test_committee,
            office=ElectionCycle.Office.SENATE,
            election_type=ElectionCycle.ElectionType.GENERAL,
            election_year="2026",
            start_date=test_election_cycle_2_start_date,
            end_date=test_election_cycle_2_end_date,
        )

        test_committee_account_id = test_committee.id
        test_aggregation_group = "GENERAL"
        test_contact_1_id = test_contact_1.id
        test_schedule_a = ScheduleA.objects.create(
            contribution_date="2023-01-02",
            contribution_amount=Decimal("100.00"),
        )
        test_transaction = Transaction.objects.create(
            committee_account_id=test_committee_account_id,
            transaction_type_identifier="INDIVIDUAL_RECEIPT",
            aggregation_group=test_aggregation_group,
            contact_1_id=test_contact_1_id,
            schedule_a_id=test_schedule_a.id,
        )

        # assert create path
        delegate_mock.assert_any_call(
            test_committee_account_id,
            test_aggregation_group,
            test_contact_1_id,
            date.fromisoformat(test_election_cycle_1_start_date),
            date.fromisoformat(test_election_cycle_1_end_date),
        )

        test_transaction.schedule_a.contribution_date = date.fromisoformat("2025-01-02")
        test_transaction.save()
        # assert update path
        delegate_mock.assert_any_call(
            test_committee_account_id,
            test_aggregation_group,
            test_contact_1_id,
            date.fromisoformat(test_election_cycle_2_start_date),
            date.fromisoformat(test_election_cycle_2_end_date),
        )

    def test_process_aggregation_for_entity_election_cycle(self):
        test_committee = CommitteeAccount.objects.create(committee_id="C00000003")
        test_contact_1 = Contact.objects.create(
            type=ContactType.INDIVIDUAL,
            last_name="test_last_name",
            first_name="test_first_name",
            committee_account_id=test_committee.id,
        )

        # Election cycle 1
        test_election_cycle_1_start_date = "2023-02-01"
        test_election_cycle_1_end_date = "2024-12-31"
        ElectionCycle.objects.create(
            committee_account=test_committee,
            office=ElectionCycle.Office.SENATE,
            election_type=ElectionCycle.ElectionType.GENERAL,
            election_year="2026",
            start_date=date.fromisoformat(test_election_cycle_1_start_date),
            end_date=date.fromisoformat(test_election_cycle_1_end_date),
        )

        # Election cycle 2
        test_election_cycle_2_start_date = "2025-02-01"
        test_election_cycle_2_end_date = "2026-12-31"
        ElectionCycle.objects.create(
            committee_account=test_committee,
            office=ElectionCycle.Office.SENATE,
            election_type=ElectionCycle.ElectionType.GENERAL,
            election_year="2026",
            start_date=date.fromisoformat(test_election_cycle_2_start_date),
            end_date=date.fromisoformat(test_election_cycle_2_end_date),
        )

        # Create transactions and verify election cycle aggregates
        test_committee_account_id = test_committee.id
        test_aggregation_group = "GENERAL"
        test_contact_1_id = test_contact_1.id

        # ======== CREATE TRANSACTION OUTSIDE ELECTION CYCLE ========

        # Transaction 0 (outside all election cycles)
        test_schedule_a_0 = ScheduleA.objects.create(
            contribution_date=date.fromisoformat("2023-01-01"),
            contribution_amount=Decimal("500.00"),
        )
        test_transaction_0 = Transaction.objects.create(
            committee_account_id=test_committee_account_id,
            transaction_type_identifier="INDIVIDUAL_RECEIPT",
            aggregation_group=test_aggregation_group,
            contact_1_id=test_contact_1_id,
            schedule_a_id=test_schedule_a_0.id,
        )
        self.assertEqual(
            test_transaction_0.entity_election_cycle_to_date,
            None,
        )

        # ======== CREATE ELECTION CYCLE 1 TRANSACTIONS ========

        # Transaction 1 (inside election cycle 1)
        test_schedule_a_1 = ScheduleA.objects.create(
            contribution_date=date.fromisoformat("2023-02-01"),
            contribution_amount=Decimal("100.00"),
        )
        test_transaction_1 = Transaction.objects.create(
            committee_account_id=test_committee_account_id,
            transaction_type_identifier="INDIVIDUAL_RECEIPT",
            aggregation_group=test_aggregation_group,
            contact_1_id=test_contact_1_id,
            schedule_a_id=test_schedule_a_1.id,
        )
        self.assertEqual(
            test_transaction_1.entity_election_cycle_to_date,
            Decimal("100.00"),
        )

        # Transaction 2 (inside election cycle 1)
        test_schedule_a_2 = ScheduleA.objects.create(
            contribution_date=date.fromisoformat("2023-02-05"),
            contribution_amount=Decimal("50.00"),
        )
        test_transaction_2 = Transaction.objects.create(
            committee_account_id=test_committee_account_id,
            transaction_type_identifier="INDIVIDUAL_RECEIPT",
            aggregation_group=test_aggregation_group,
            contact_1_id=test_contact_1_id,
            schedule_a_id=test_schedule_a_2.id,
        )
        self.assertEqual(
            test_transaction_2.entity_election_cycle_to_date,
            Decimal("150.00"),
        )

        # Transaction 3 (inside election cycle 1)
        test_schedule_a_3 = ScheduleA.objects.create(
            contribution_date=date.fromisoformat("2023-02-10"),
            contribution_amount=Decimal("25.00"),
        )
        test_transaction_3 = Transaction.objects.create(
            committee_account_id=test_committee_account_id,
            transaction_type_identifier="INDIVIDUAL_RECEIPT",
            aggregation_group=test_aggregation_group,
            contact_1_id=test_contact_1_id,
            schedule_a_id=test_schedule_a_3.id,
        )
        self.assertEqual(
            test_transaction_3.entity_election_cycle_to_date,
            Decimal("175.00"),
        )

        # ======== CREATE ELECTION CYCLE 2 TRANSACTIONS ========

        # Transaction 4 (inside election cycle 2)
        test_schedule_a_4 = ScheduleA.objects.create(
            contribution_date=date.fromisoformat("2025-02-01"),
            contribution_amount=Decimal("500.00"),
        )
        test_transaction_4 = Transaction.objects.create(
            committee_account_id=test_committee_account_id,
            transaction_type_identifier="INDIVIDUAL_RECEIPT",
            aggregation_group=test_aggregation_group,
            contact_1_id=test_contact_1_id,
            schedule_a_id=test_schedule_a_4.id,
        )
        self.assertEqual(
            test_transaction_4.entity_election_cycle_to_date,
            Decimal("500.00"),
        )

        # Transaction 5 (inside election cycle 2)
        test_schedule_a_5 = ScheduleA.objects.create(
            contribution_date=date.fromisoformat("2025-02-05"),
            contribution_amount=Decimal("400.00"),
        )
        test_transaction_5 = Transaction.objects.create(
            committee_account_id=test_committee_account_id,
            transaction_type_identifier="INDIVIDUAL_RECEIPT",
            aggregation_group=test_aggregation_group,
            contact_1_id=test_contact_1_id,
            schedule_a_id=test_schedule_a_5.id,
        )
        self.assertEqual(
            test_transaction_5.entity_election_cycle_to_date,
            Decimal("900.00"),
        )

        # Transaction 6 (inside election cycle 2)
        test_schedule_a_6 = ScheduleA.objects.create(
            contribution_date=date.fromisoformat("2025-02-10"),
            contribution_amount=Decimal("300.00"),
        )
        test_transaction_6 = Transaction.objects.create(
            committee_account_id=test_committee_account_id,
            transaction_type_identifier="INDIVIDUAL_RECEIPT",
            aggregation_group=test_aggregation_group,
            contact_1_id=test_contact_1_id,
            schedule_a_id=test_schedule_a_6.id,
        )
        self.assertEqual(
            test_transaction_6.entity_election_cycle_to_date,
            Decimal("1200.00"),
        )

        # ======== ADD ELECTION CYCLE 1 TRANSACTION ========
        self.assertEqual(
            test_transaction_0.entity_election_cycle_to_date,
            None,
        )
        self.assertEqual(
            test_transaction_1.entity_election_cycle_to_date,
            Decimal("100.00"),
        )
        self.assertEqual(
            test_transaction_2.entity_election_cycle_to_date,
            Decimal("150.00"),
        )
        self.assertEqual(
            test_transaction_3.entity_election_cycle_to_date,
            Decimal("175.00"),
        )
        # Transaction 1a (inside election cycle 1)
        test_schedule_a_1a = ScheduleA.objects.create(
            contribution_date=date.fromisoformat("2023-02-02"),
            contribution_amount=Decimal("10.00"),
        )
        test_transaction_1a = Transaction.objects.create(
            committee_account_id=test_committee_account_id,
            transaction_type_identifier="INDIVIDUAL_RECEIPT",
            aggregation_group=test_aggregation_group,
            contact_1_id=test_contact_1_id,
            schedule_a_id=test_schedule_a_1a.id,
        )
        test_transaction_1.refresh_from_db()
        test_transaction_1a.refresh_from_db()
        test_transaction_2.refresh_from_db()
        test_transaction_3.refresh_from_db()
        self.assertEqual(
            test_transaction_0.entity_election_cycle_to_date,
            None,
        )
        self.assertEqual(
            test_transaction_1.entity_election_cycle_to_date,
            Decimal("100.00"),
        )
        self.assertEqual(
            test_transaction_1a.entity_election_cycle_to_date,
            Decimal("110.00"),
        )
        self.assertEqual(
            test_transaction_2.entity_election_cycle_to_date,
            Decimal("160.00"),
        )
        self.assertEqual(
            test_transaction_3.entity_election_cycle_to_date,
            Decimal("185.00"),
        )

        # ======== ADD ELECTION CYCLE 2 TRANSACTION ========
        self.assertEqual(
            test_transaction_4.entity_election_cycle_to_date,
            Decimal("500.00"),
        )
        self.assertEqual(
            test_transaction_5.entity_election_cycle_to_date,
            Decimal("900.00"),
        )
        self.assertEqual(
            test_transaction_6.entity_election_cycle_to_date,
            Decimal("1200.00"),
        )
        # Transaction 4a (inside election cycle 2)
        test_schedule_a_4a = ScheduleA.objects.create(
            contribution_date=date.fromisoformat("2025-02-02"),
            contribution_amount=Decimal("75.00"),
        )
        test_transaction_4a = Transaction.objects.create(
            committee_account_id=test_committee_account_id,
            transaction_type_identifier="INDIVIDUAL_RECEIPT",
            aggregation_group=test_aggregation_group,
            contact_1_id=test_contact_1_id,
            schedule_a_id=test_schedule_a_4a.id,
        )
        test_transaction_4.refresh_from_db()
        test_transaction_4a.refresh_from_db()
        test_transaction_5.refresh_from_db()
        test_transaction_6.refresh_from_db()
        self.assertEqual(
            test_transaction_4.entity_election_cycle_to_date,
            Decimal("500.00"),
        )
        self.assertEqual(
            test_transaction_4a.entity_election_cycle_to_date,
            Decimal("575.00"),
        )
        self.assertEqual(
            test_transaction_5.entity_election_cycle_to_date,
            Decimal("975.00"),
        )
        self.assertEqual(
            test_transaction_6.entity_election_cycle_to_date,
            Decimal("1275.00"),
        )

        # ======== UPDATE ELECTION CYCLE 1 TRANSACTION ========
        self.assertEqual(
            test_transaction_1.entity_election_cycle_to_date,
            Decimal("100.00"),
        )
        self.assertEqual(
            test_transaction_1a.entity_election_cycle_to_date,
            Decimal("110.00"),
        )
        self.assertEqual(
            test_transaction_2.entity_election_cycle_to_date,
            Decimal("160.00"),
        )
        self.assertEqual(
            test_transaction_3.entity_election_cycle_to_date,
            Decimal("185.00"),
        )
        old_snapshot = {"effective_amount": Decimal("10.00")}
        test_transaction_1a.schedule_a.contribution_amount = Decimal("15.00")
        test_transaction_1a.schedule_a.save()
        test_transaction_1a._passed_old_snapshot = old_snapshot
        test_transaction_1a.save()
        test_transaction_1.refresh_from_db()
        test_transaction_1a.refresh_from_db()
        test_transaction_2.refresh_from_db()
        test_transaction_3.refresh_from_db()
        self.assertEqual(
            test_transaction_1.entity_election_cycle_to_date,
            Decimal("100.00"),
        )
        self.assertEqual(
            test_transaction_1a.entity_election_cycle_to_date,
            Decimal("115.00"),
        )
        self.assertEqual(
            test_transaction_2.entity_election_cycle_to_date,
            Decimal("165.00"),
        )
        self.assertEqual(
            test_transaction_3.entity_election_cycle_to_date,
            Decimal("190.00"),
        )

        # ======== DELETE ELECTION CYCLE 1 TRANSACTION ========
        self.assertEqual(
            test_transaction_1.entity_election_cycle_to_date,
            Decimal("100.00"),
        )
        self.assertEqual(
            test_transaction_1a.entity_election_cycle_to_date,
            Decimal("115.00"),
        )
        self.assertEqual(
            test_transaction_2.entity_election_cycle_to_date,
            Decimal("165.00"),
        )
        self.assertEqual(
            test_transaction_3.entity_election_cycle_to_date,
            Decimal("190.00"),
        )
        test_transaction_1a.delete()
        test_transaction_1.refresh_from_db()
        test_transaction_2.refresh_from_db()
        test_transaction_3.refresh_from_db()
        self.assertEqual(
            test_transaction_1.entity_election_cycle_to_date,
            Decimal("100.00"),
        )
        self.assertEqual(
            test_transaction_2.entity_election_cycle_to_date,
            Decimal("150.00"),
        )
        self.assertEqual(
            test_transaction_3.entity_election_cycle_to_date,
            Decimal("175.00"),
        )

        # ======== CREATE TRANSACTION OUTSIDE ELECTION CYCLE ========

        # Transaction 7 (outside all election cycles)
        test_schedule_a_7 = ScheduleA.objects.create(
            contribution_date=date.fromisoformat("2023-01-02"),
            contribution_amount=Decimal("1000.00"),
        )
        test_transaction_7 = Transaction.objects.create(
            committee_account_id=test_committee_account_id,
            transaction_type_identifier="INDIVIDUAL_RECEIPT",
            aggregation_group=test_aggregation_group,
            contact_1_id=test_contact_1_id,
            schedule_a_id=test_schedule_a_7.id,
        )
        self.assertEqual(
            test_transaction_7.entity_election_cycle_to_date,
            None,
        )

        # ======== VERIFY ENTITY/ELECTION_CYCLE AGGREGATES ========

        # test_transaction_0
        test_transaction_0.refresh_from_db()
        self.assertEqual(
            test_transaction_0.aggregate,
            Decimal("500.00"),
        )
        self.assertEqual(
            test_transaction_0.entity_election_cycle_to_date,
            None,
        )

        # test_transaction_1
        test_transaction_1.refresh_from_db()
        self.assertEqual(
            test_transaction_1.aggregate,
            Decimal("1600.00"),
        )
        self.assertEqual(
            test_transaction_1.entity_election_cycle_to_date,
            Decimal("100.00"),
        )

        # test_transaction_2
        test_transaction_2.refresh_from_db()
        self.assertEqual(
            test_transaction_2.aggregate,
            Decimal("1650.00"),
        )
        self.assertEqual(
            test_transaction_2.entity_election_cycle_to_date,
            Decimal("150.00"),
        )

        # test_transaction_3
        test_transaction_3.refresh_from_db()
        self.assertEqual(
            test_transaction_3.aggregate,
            Decimal("1675.00"),
        )
        self.assertEqual(
            test_transaction_3.entity_election_cycle_to_date,
            Decimal("175.00"),
        )

        # test_transaction_4
        test_transaction_4.refresh_from_db()
        self.assertEqual(
            test_transaction_4.aggregate,
            Decimal("500.00"),
        )
        self.assertEqual(
            test_transaction_4.entity_election_cycle_to_date,
            Decimal("500.00"),
        )

        # test_transaction_5
        test_transaction_5.refresh_from_db()
        self.assertEqual(
            test_transaction_5.aggregate,
            Decimal("975.00"),
        )
        self.assertEqual(
            test_transaction_5.entity_election_cycle_to_date,
            Decimal("975.00"),
        )

        # test_transaction_6
        test_transaction_6.refresh_from_db()
        self.assertEqual(
            test_transaction_6.aggregate,
            Decimal("1275.00"),
        )
        self.assertEqual(
            test_transaction_6.entity_election_cycle_to_date,
            Decimal("1275.00"),
        )

        # test_transaction_7
        test_transaction_7.refresh_from_db()
        self.assertEqual(
            test_transaction_7.aggregate,
            Decimal("1500.00"),
        )
        self.assertEqual(
            test_transaction_7.entity_election_cycle_to_date,
            None,
        )
