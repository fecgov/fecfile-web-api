import uuid
from django.core.exceptions import ValidationError
from django.test import TestCase
from fecfiler.committee_accounts.models import CommitteeAccount
from ..models import ElectionCycle


class ElectionCycleTestCase(TestCase):

    def setUp(self):
        self.committee = CommitteeAccount.objects.create(committee_id="C00000000")

        self.valid_election_cycle = ElectionCycle(
            id=uuid.UUID("94777fb3-6d3a-4e2c-87dc-5e6ed326e65b"),
            committee_account=self.committee,
            office=ElectionCycle.Office.HOUSE,
            election_type=ElectionCycle.ElectionType.GENERAL,
            election_year="2024",
            start_date="2023-01-01",
            end_date="2024-12-31",
        )

    def test_save_and_get_election_cycle(self):
        self.valid_election_cycle.save()
        cycle_from_db = ElectionCycle.objects.get(
            id=uuid.UUID("94777fb3-6d3a-4e2c-87dc-5e6ed326e65b")
        )

        self.assertIsInstance(cycle_from_db, ElectionCycle)
        self.assertEqual(cycle_from_db.office, "House")
        self.assertEqual(cycle_from_db.election_type, "General")
        self.assertEqual(cycle_from_db.election_year, "2024")
        self.assertEqual(cycle_from_db.committee_account, self.committee)

    def test_string_representation(self):
        self.valid_election_cycle.save()
        self.assertEqual(str(self.valid_election_cycle), "2024 House (General)")

    def test_election_year_regex_validation(self):
        invalid_years = ["24", "20244", "YYYY", "202a"]

        for invalid_year in invalid_years:
            cycle = ElectionCycle(
                committee_account=self.committee,
                office=ElectionCycle.Office.HOUSE,
                election_type=ElectionCycle.ElectionType.GENERAL,
                election_year=invalid_year,
                start_date="2023-01-01",
                end_date="2024-12-31",
            )
            with self.assertRaises(ValidationError):
                cycle.full_clean()

    def test_invalid_choices(self):
        cycle = ElectionCycle(
            committee_account=self.committee,
            office="GOVERNOR",
            election_type="PRIMARY",
            election_year="2024",
            start_date="2023-01-01",
            end_date="2024-12-31",
        )
        with self.assertRaises(ValidationError):
            cycle.full_clean()
