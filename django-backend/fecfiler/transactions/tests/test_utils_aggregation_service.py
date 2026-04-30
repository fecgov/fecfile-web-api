from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch
from django.test import TestCase
from fecfiler.transactions.managers import Schedule
from fecfiler.transactions.utils_aggregation_service import (
    _get_previous_aggregate_value,
    _should_cascade_unitemization_service,
    apply_delete_delta_aggregates,
    update_aggregates_for_affected_transactions,
)


class AggregationServiceUnitTestCase(TestCase):
    def test_get_previous_aggregate_value_defaults_to_zero(self):
        base_qs = MagicMock()
        previous_value_query = (
            base_qs.filter.return_value.order_by.return_value.values_list.return_value
        )
        previous_value_query.first.return_value = None

        previous = _get_previous_aggregate_value(
            base_qs,
            "aggregate",
            date(2024, 1, 2),
            datetime(2024, 1, 2, 12, 0, 0),
        )

        self.assertEqual(previous, Decimal("0"))

    def test_get_previous_aggregate_value_coerces_non_decimal(self):
        base_qs = MagicMock()
        previous_value_query = (
            base_qs.filter.return_value.order_by.return_value.values_list.return_value
        )
        previous_value_query.first.return_value = 7

        previous = _get_previous_aggregate_value(
            base_qs,
            "aggregate",
            date(2024, 1, 2),
            datetime(2024, 1, 2, 12, 0, 0),
        )

        self.assertEqual(previous, Decimal("7"))

    @patch("fecfiler.transactions.utils_aggregation_service.has_itemized_children")
    def test_should_cascade_unitemization_service_threshold_drop(self, has_children_mock):
        has_children_mock.return_value = False
        instance = MagicMock()
        instance.force_itemized = None
        instance.aggregate = Decimal("199.00")

        self.assertTrue(
            _should_cascade_unitemization_service(
                instance,
                Decimal("250.00"),
                uses_itemization_threshold=True,
            )
        )

    def test_should_cascade_unitemization_service_force_itemized_blocks_cascade(
        self,
    ):
        instance = MagicMock()
        instance.force_itemized = True
        instance.aggregate = Decimal("199.00")

        self.assertFalse(
            _should_cascade_unitemization_service(
                instance,
                Decimal("250.00"),
                uses_itemization_threshold=True,
            )
        )

    def test_update_aggregates_for_affected_transactions_rejects_invalid_action(self):
        with self.assertRaises(ValueError):
            update_aggregates_for_affected_transactions(
                transaction_model=MagicMock(),
                instance=MagicMock(),
                action="invalid",
            )

    @patch(
        "fecfiler.transactions.utils_aggregation_service."
        "recalculate_aggregates_for_transaction"
    )
    def test_update_aggregates_delete_is_noop(self, recalc_mock):
        update_aggregates_for_affected_transactions(
            transaction_model=MagicMock(),
            instance=MagicMock(),
            action="delete",
        )

        recalc_mock.assert_not_called()

    @patch("fecfiler.transactions.utils_aggregation_service._update_suffix_delta")
    def test_apply_delete_delta_aggregates_for_contact_schedule(
        self, update_suffix_mock
    ):
        transaction_model = MagicMock()
        first_qs = MagicMock()
        second_qs = MagicMock()
        transaction_model.objects.filter.return_value = first_qs
        first_qs.filter.return_value = second_qs

        apply_delete_delta_aggregates(
            transaction_model,
            {
                "schedule": Schedule.A,
                "date": date(2024, 1, 1),
                "created": datetime(2024, 1, 1, 12, 0, 0),
                "contact_1_id": "contact-1",
                "aggregation_group": "GENERAL",
                "effective_amount": Decimal("25.00"),
            },
        )

        update_suffix_mock.assert_called_once()
        call_args = update_suffix_mock.call_args[0]
        self.assertEqual(call_args[0], second_qs)
        self.assertEqual(call_args[1], "aggregate")
        self.assertEqual(call_args[4], Decimal("-25.00"))

    @patch("fecfiler.transactions.utils_aggregation_service._update_suffix_delta")
    def test_apply_delete_delta_aggregates_for_schedule_e(self, update_suffix_mock):
        transaction_model = MagicMock()
        first_qs = MagicMock()
        second_qs = MagicMock()
        transaction_model.objects.filter.return_value = first_qs
        first_qs.filter.return_value = second_qs

        apply_delete_delta_aggregates(
            transaction_model,
            {
                "schedule": Schedule.E,
                "date": date(2024, 1, 1),
                "created": datetime(2024, 1, 1, 12, 0, 0),
                "election_code": "H2024",
                "candidate_office": "H",
                "candidate_state": "AK",
                "candidate_district": "01",
                "aggregation_group": "INDEPENDENT_EXPENDITURE",
                "committee_account_id": "committee-1",
                "effective_amount": Decimal("40.00"),
            },
        )

        update_suffix_mock.assert_called_once()
        call_args = update_suffix_mock.call_args[0]
        self.assertEqual(call_args[0], second_qs)
        self.assertEqual(call_args[1], "_calendar_ytd_per_election_office")
        self.assertEqual(call_args[4], Decimal("-40.00"))
