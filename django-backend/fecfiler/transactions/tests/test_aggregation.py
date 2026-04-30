from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from fecfiler.transactions.aggregation import (
    process_aggregation_by_payee_candidate,
    process_aggregation_for_debts,
    process_aggregation_for_election,
    process_aggregation_for_entity,
    reaggregate_after_report_deletion,
    schedule_a_over_two_hundred_types,
)


class AggregationDirectFunctionTestCase(SimpleTestCase):
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

        shared_entity_qs.filter.assert_called_once_with(
            date__gte=date(2024, 1, 15)
        )
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
