from django.test import TestCase
from unittest.mock import MagicMock, patch
from fecfiler.devops.utils.locust_data_generator import LocustDataGenerator, save_json


class LocustDataGeneratorTestCase(TestCase):
    def setUp(self):
        self.committee = MagicMock()
        self.committee.id = "test_committee_id"
        self.generator = LocustDataGenerator(self.committee)

    @patch("fecfiler.devops.utils.locust_data_generator.create_form3x")
    def test_generate_form_3x(self, mock_create_form3x):
        test_f3x_count = 3
        mock_create_form3x.return_value = MagicMock()
        result = self.generator.generate_form_3x(test_f3x_count)
        self.assertEqual(len(result), test_f3x_count)
        self.assertTrue(all(isinstance(x, MagicMock) for x in result))

    def test_generate_contacts(self):
        test_contacts_count = 3
        contacts = self.generator.generate_contacts(test_contacts_count)
        self.assertEqual(len(contacts), test_contacts_count)
        for contact in contacts:
            self.assertEqual(contact.committee_account_id, self.committee.id)
            self.assertEqual(contact.type, "IND")
            self.assertEqual(contact.city, "Testville")
            self.assertEqual(contact.state, "AK")
            self.assertEqual(contact.zip, "12345")
            self.assertEqual(contact.country, "USA")
            self.assertEqual(contact.employer, "Business Inc.")
            self.assertEqual(contact.occupation, "Job")

    @patch("fecfiler.devops.utils.locust_data_generator.create_schedule_a")
    def test_generate_single_transactions(self, mock_create_schedule_a):
        test_transaction_count = 4
        test_reports = [MagicMock(coverage_from_date="2020-01-01")]
        test_contacts = [MagicMock()]
        mock_create_schedule_a.return_value = MagicMock()
        result = self.generator.generate_single_transactions(
            test_transaction_count, test_reports, test_contacts
        )
        self.assertEqual(len(result), test_transaction_count)
        self.assertTrue(all(isinstance(x, MagicMock) for x in result))

    @patch("fecfiler.devops.utils.locust_data_generator.create_schedule_a")
    def test_generate_triple_transactions(self, mock_create_schedule_a):
        # Each triple creates 3 transactions, but only the first is returned
        mock_a = MagicMock()
        mock_b = MagicMock()
        mock_c = MagicMock()
        mock_a.id = 1
        mock_b.id = 2
        test_transaction_count = 2
        mock_create_schedule_a.side_effect = [
            mock_a,
            mock_b,
            mock_c,
        ] * test_transaction_count
        test_reports = [MagicMock(coverage_from_date="2020-01-01")]
        test_contacts = [MagicMock()]
        result = self.generator.generate_triple_transactions(
            test_transaction_count, test_reports, test_contacts
        )
        self.assertEqual(len(result), test_transaction_count)
        self.assertTrue(all(isinstance(x, MagicMock) for x in result))
