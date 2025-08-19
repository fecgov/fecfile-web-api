from django.test import TestCase
from unittest.mock import patch, MagicMock
from fecfiler.devops.utils.locust_data_generator import LocustDataGenerator
from fecfiler.reports.models import Report
from fecfiler.contacts.models import Contact
from fecfiler.transactions.schedule_a.models import ScheduleA
from fecfiler.transactions.schedule_b.models import ScheduleB
from fecfiler.committee_accounts.models import CommitteeAccount
import uuid


def add_schedule_a_to_transaction(transaction_list):
    for transaction in transaction_list:
        transaction.schedule_a = ScheduleA(
            **{
                "contribution_purpose_descrip": uuid.uuid4(),
            }
        )
    return transaction_list


def add_schedule_b_to_transaction(transaction_list):
    for transaction in transaction_list:
        transaction.schedule_b = ScheduleB(
            **{
                "expenditure_purpose_descrip": uuid.uuid4(),
            }
        )
    return transaction_list


class LocustDataGeneratorTestCase(TestCase):
    def setUp(self):
        test_committee_account = CommitteeAccount()
        test_committee_account.id = uuid.uuid4()
        self.locust_data_generator = LocustDataGenerator(test_committee_account)

    @patch(
        "fecfiler.devops.utils.locust_data_generator.Form3X.objects.bulk_create",
        side_effect=lambda x: x,
    )
    @patch(
        "fecfiler.devops.utils.locust_data_generator.Report.objects.bulk_create",
        side_effect=lambda x: x,
    )
    def test_generate_form_3x(self, mock_report_bulk_create, mock_form3x_bulk_create):
        result = self.locust_data_generator.generate_form_3x(3)
        self.assertEqual(len(result), 3)
        mock_report_bulk_create.assert_called_with(result)
        for report in result:
            self.assertIsNotNone(report.id)
            self.assertEqual(report.form_type, "F3XN")
            self.assertEqual(
                report.committee_account_id, self.locust_data_generator.committee.id
            )

    @patch(
        "fecfiler.devops.utils.locust_data_generator.Contact.objects.bulk_create",
        side_effect=lambda x: x,
    )
    def test_generate_contacts(self, mock_contact_bulk_create):
        result = self.locust_data_generator.generate_contacts(3)
        self.assertEqual(len(result), 3)
        mock_contact_bulk_create.assert_called_with(result)
        for contact in result:
            self.assertIsNotNone(contact.id)
            self.assertEqual(
                contact.committee_account_id, self.locust_data_generator.committee.id
            )
            self.assertEqual(contact.type, "IND")

    @patch(
        "fecfiler.devops.utils.locust_data_generator.ScheduleA.objects.bulk_create",
        side_effect=lambda x: x,
    )
    @patch(
        "fecfiler.devops.utils.locust_data_generator.Transaction.objects.bulk_create",
        side_effect=add_schedule_a_to_transaction,
    )
    @patch(
        "fecfiler.devops.utils.locust_data_generator"
        ".ReportTransaction.objects.bulk_create"
    )
    def test_generate_single_schedule_a_transactions(
        self,
        mock_report_transaction_bulk_create,
        mock_transaction_bulk_create,
        mock_schedule_a_bulk_create,
    ):
        test_report = Report(
            **{
                "id": uuid.uuid4(),
                "form_type": "F3XN",
                "committee_account_id": self.locust_data_generator.committee.id,
                "coverage_from_date": "2025-01-01",
                "coverage_through_date": "2025-03-31",
                "report_code": "Q1",
            }
        )
        test_reports = [test_report]

        test_contact = Contact(
            **{
                "id": uuid.uuid4(),
                "committee_account_id": self.locust_data_generator.committee.id,
                "type": "IND",
            }
        )
        test_contacts = [test_contact]

        result = self.locust_data_generator.generate_single_schedule_a_transactions(
            3, test_reports, test_contacts
        )
        self.assertEqual(len(result), 3)
        mock_transaction_bulk_create.assert_called_with(result)
        for transaction in result:
            self.assertIsNotNone(transaction.id)
            self.assertEqual(
                transaction.transaction_type_identifier, "INDIVIDUAL_RECEIPT"
            )
            self.assertEqual(
                transaction.committee_account_id, self.locust_data_generator.committee.id
            )
            self.assertEqual(transaction.contact_1_id, test_contact.id)
            self.assertEqual(transaction.aggregation_group, "GENERAL")
            self.assertEqual(transaction.form_type, "SA11AI")

    @patch(
        "fecfiler.devops.utils.locust_data_generator.Transaction.objects.bulk_update",
    )
    @patch(
        "fecfiler.devops.utils.locust_data_generator"
        ".LocustDataGenerator.generate_single_schedule_a_transactions"
    )
    def test_generate_triple_schedule_a_transactions(
        self,
        mock_generate_single_schedule_a_transactions,
        mock_transaction_bulk_update,
    ):
        mock_tier1_transaction = MagicMock(id=1, parent_transaction_id=None)
        mock_tier2_transaction = MagicMock(id=2, parent_transaction_id=None)
        mock_tier3_transaction = MagicMock(id=3, parent_transaction_id=None)

        mock_generate_single_schedule_a_transactions.side_effect = [
            [mock_tier1_transaction],
            [mock_tier2_transaction],
            [mock_tier3_transaction],
        ]

        result = self.locust_data_generator.generate_triple_schedule_a_transactions(
            1, [], []
        )
        self.assertEqual(len(result), 1)
        self.assertEqual(mock_tier3_transaction.id, 3)
        self.assertEqual(mock_tier3_transaction.parent_transaction_id, 2)
        self.assertEqual(mock_tier2_transaction.id, 2)
        self.assertEqual(mock_tier2_transaction.parent_transaction_id, 1)
        self.assertEqual(mock_tier1_transaction.id, 1)
        self.assertEqual(mock_tier1_transaction.parent_transaction_id, None)

    @patch(
        "fecfiler.devops.utils.locust_data_generator.ScheduleB.objects.bulk_create",
        side_effect=lambda x: x,
    )
    @patch(
        "fecfiler.devops.utils.locust_data_generator.Transaction.objects.bulk_create",
        side_effect=add_schedule_b_to_transaction,
    )
    @patch(
        "fecfiler.devops.utils.locust_data_generator"
        ".ReportTransaction.objects.bulk_create"
    )
    def test_generate_single_schedule_b_transactions(
        self,
        mock_report_transaction_bulk_create,
        mock_transaction_bulk_create,
        mock_schedule_b_bulk_create,
    ):
        test_report = Report(
            **{
                "id": uuid.uuid4(),
                "form_type": "F3XN",
                "committee_account_id": self.locust_data_generator.committee.id,
                "coverage_from_date": "2025-01-01",
                "coverage_through_date": "2025-03-31",
                "report_code": "Q1",
            }
        )
        test_reports = [test_report]

        test_contact = Contact(
            **{
                "id": uuid.uuid4(),
                "committee_account_id": self.locust_data_generator.committee.id,
                "type": "IND",
            }
        )
        test_contacts = [test_contact]

        result = self.locust_data_generator.generate_single_schedule_b_transactions(
            3, test_reports, test_contacts
        )
        self.assertEqual(len(result), 3)
        mock_transaction_bulk_create.assert_called_with(result)
        for transaction in result:
            self.assertIsNotNone(transaction.id)
            self.assertEqual(
                transaction.transaction_type_identifier, "OPERATING_EXPENDITURE"
            )
            self.assertEqual(
                transaction.committee_account_id, self.locust_data_generator.committee.id
            )
            self.assertEqual(transaction.contact_1_id, test_contact.id)
            self.assertEqual(transaction.aggregation_group, "GENERAL")
            self.assertEqual(transaction.form_type, "SB21B")

    @patch(
        "fecfiler.devops.utils.locust_data_generator.Transaction.objects.bulk_update",
    )
    @patch(
        "fecfiler.devops.utils.locust_data_generator"
        ".LocustDataGenerator.generate_single_schedule_b_transactions"
    )
    def test_generate_triple_schedule_b_transactions(
        self,
        mock_generate_single_schedule_b_transactions,
        mock_transaction_bulk_update,
    ):
        mock_tier1_transaction = MagicMock(id=1, parent_transaction_id=None)
        mock_tier2_transaction = MagicMock(id=2, parent_transaction_id=None)
        mock_tier3_transaction = MagicMock(id=3, parent_transaction_id=None)

        mock_generate_single_schedule_b_transactions.side_effect = [
            [mock_tier1_transaction],
            [mock_tier2_transaction],
            [mock_tier3_transaction],
        ]

        result = self.locust_data_generator.generate_triple_schedule_b_transactions(
            1, [], []
        )
        self.assertEqual(len(result), 1)
        self.assertEqual(mock_tier3_transaction.id, 3)
        self.assertEqual(mock_tier3_transaction.parent_transaction_id, 2)
        self.assertEqual(mock_tier2_transaction.id, 2)
        self.assertEqual(mock_tier2_transaction.parent_transaction_id, 1)
        self.assertEqual(mock_tier1_transaction.id, 1)
        self.assertEqual(mock_tier1_transaction.parent_transaction_id, None)
