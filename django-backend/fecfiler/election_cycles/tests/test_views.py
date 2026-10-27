from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.user.models import User
from ..models import ElectionCycle
from fecfiler.reports.form_3.models import Form3


class ElectionCyclesViewSetTestCase(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.committee = CommitteeAccount.objects.create(committee_id="C00000000")
        self.user = User.objects.create(email="test@fec.gov", username="gov")

        self.client.force_authenticate(user=self.user)
        session = self.client.session
        session["committee_uuid"] = str(self.committee.id)
        session["committee_id"] = str(self.committee.committee_id)
        session.save()

        self.cycle_1 = ElectionCycle.objects.create(
            committee_account=self.committee,
            office=ElectionCycle.Office.HOUSE,
            election_type=ElectionCycle.ElectionType.GENERAL,
            election_year="2024",
            start_date="2023-01-01",
            end_date="2024-12-31",
        )

        self.valid_payload = {
            "office": "Senate",
            "election_type": "General",
            "election_year": "2026",
            "start_date": "2025-01-01",
            "end_date": "2026-12-31",
        }

    def test_list_election_cycles(self):
        response = self.client.get("/api/v1/election-cycles/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 1)

        result = response.data["results"][0]
        self.assertEqual(result["id"], str(self.cycle_1.id))
        self.assertIn("has_form3", result)
        self.assertFalse(result["has_form3"])

    def test_retrieve_election_cycle(self):
        response = self.client.get(f"/api/v1/election-cycles/{self.cycle_1.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["office"], "House")
        self.assertEqual(response.data["election_year"], "2024")
        self.assertIn("has_form3", response.data)
        self.assertFalse(response.data["has_form3"])

    def test_create_election_cycle(self):
        payload = {
            **self.valid_payload,
            "has_form3": True,
        }

        response = self.client.post(
            "/api/v1/election-cycles/",
            data=payload,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ElectionCycle.objects.count(), 2)

        created_cycle = ElectionCycle.objects.get(id=response.data["id"])
        self.assertEqual(created_cycle.committee_account, self.committee)
        self.assertFalse(Form3.objects.filter(election_cycle=created_cycle).exists())

    def test_update_election_cycle(self):
        update_data = {
            **self.valid_payload,
            "office": "Senate",
            "has_form3": True,
        }

        response = self.client.put(
            f"/api/v1/election-cycles/{self.cycle_1.id}/",
            data=update_data,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.cycle_1.refresh_from_db()
        self.assertEqual(self.cycle_1.office, "Senate")
        self.assertIn("has_form3", response.data)
        self.assertFalse(response.data["has_form3"])

    def test_destroy_election_cycle(self):
        response = self.client.delete(f"/api/v1/election-cycles/{self.cycle_1.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ElectionCycle.objects.filter(id=self.cycle_1.id).exists())

    def test_check_overlap_missing_params(self):
        response = self.client.get("/api/v1/election-cycles/check-overlap/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["error"],
            "Both start_date and end_date query parameters are required.",
        )

        response = self.client.get(
            "/api/v1/election-cycles/check-overlap/?start_date=2023-01-01"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_check_overlap_no_overlap(self):
        response = self.client.get(
            "/api/v1/election-cycles/check-overlap/",
            {"start_date": "2025-01-01", "end_date": "2026-12-31"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["start_date"])
        self.assertFalse(response.data["end_date"])

    def test_check_overlap_start_date_fails(self):
        response = self.client.get(
            "/api/v1/election-cycles/check-overlap/",
            {"start_date": "2024-06-01", "end_date": "2025-12-31"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["start_date"])
        self.assertFalse(response.data["end_date"])

    def test_check_overlap_end_date_fails(self):
        response = self.client.get(
            "/api/v1/election-cycles/check-overlap/",
            {"start_date": "2022-01-01", "end_date": "2023-06-01"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["start_date"])
        self.assertTrue(response.data["end_date"])

    def test_check_overlap_enclosing_range_both_fail(self):
        response = self.client.get(
            "/api/v1/election-cycles/check-overlap/",
            {"start_date": "2022-01-01", "end_date": "2025-12-31"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["start_date"])
        self.assertTrue(response.data["end_date"])

    def test_check_overlap_with_exclude_id(self):
        response = self.client.get(
            "/api/v1/election-cycles/check-overlap/",
            {
                "start_date": "2023-01-01",
                "end_date": "2024-12-31",
                "exclude_id": str(self.cycle_1.id),
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["start_date"])
        self.assertFalse(response.data["end_date"])

    def test_cannot_get_other_committee_election_cycles(self):
        other_committee = CommitteeAccount.objects.create(committee_id="C00000001")
        other_cycle = ElectionCycle.objects.create(
            committee_account=other_committee,
            office=ElectionCycle.Office.HOUSE,
            election_type=ElectionCycle.ElectionType.GENERAL,
            election_year="2024",
            start_date="2023-01-01",
            end_date="2024-12-31",
        )

        response = self.client.get("/api/v1/election-cycles/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]
        self.assertEqual(len(results), 1)
        self.assertNotEqual(results[0]["id"], str(other_cycle.id))
        self.assertIn("has_form3", results[0])

        response = self.client.get(f"/api/v1/election-cycles/{other_cycle.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_cannot_update_other_committee_election_cycle(self):
        other_committee = CommitteeAccount.objects.create(committee_id="C00000001")
        other_cycle = ElectionCycle.objects.create(
            committee_account=other_committee,
            office=ElectionCycle.Office.HOUSE,
            election_type=ElectionCycle.ElectionType.GENERAL,
            election_year="2024",
            start_date="2023-01-01",
            end_date="2024-12-31",
        )

        update_payload = {
            **self.valid_payload,
            "office": "Senate",
        }
        response = self.client.put(
            f"/api/v1/election-cycles/{other_cycle.id}/",
            data=update_payload,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        other_cycle.refresh_from_db()
        self.assertEqual(other_cycle.office, "House")

    def test_cannot_create_other_committee_election_cycle(self):
        other_committee = CommitteeAccount.objects.create(committee_id="C00000001")

        payload_with_other_committee = {
            **self.valid_payload,
            "committee_account": str(other_committee.id),
        }

        response = self.client.post(
            "/api/v1/election-cycles/",
            data=payload_with_other_committee,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        created_cycle = ElectionCycle.objects.get(id=response.data["id"])
        self.assertEqual(created_cycle.committee_account, self.committee)
        self.assertNotEqual(created_cycle.committee_account, other_committee)

    def test_find_by_coverage_returns_containing_cycle(self):
        response = self.client.get(
            "/api/v1/election-cycles/find-by-coverage/",
            {
                "start_date": "2023-06-01",
                "end_date": "2024-06-30",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["needs_cycle"])
        self.assertEqual(response.data["election_cycle"]["id"], str(self.cycle_1.id))
        self.assertEqual(response.data["election_cycle"]["office"], "House")
        self.assertEqual(response.data["election_cycle"]["election_year"], "2024")
        self.assertIn("has_form3", response.data["election_cycle"])
        self.assertFalse(response.data["election_cycle"]["has_form3"])
        self.assertNotIn("next_election_cycle", response.data)

    def test_find_by_coverage_missing_params(self):
        response = self.client.get(
            "/api/v1/election-cycles/find-by-coverage/",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["error"],
            "Both start_date and end_date query parameters "
            "are required and must be valid dates.",
        )

    def test_find_by_coverage_missing_end_date(self):
        response = self.client.get(
            "/api/v1/election-cycles/find-by-coverage/",
            {"start_date": "2023-06-01"},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_find_by_coverage_missing_start_date(self):
        response = self.client.get(
            "/api/v1/election-cycles/find-by-coverage/",
            {"end_date": "2024-06-30"},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_find_by_coverage_invalid_dates(self):
        response = self.client.get(
            "/api/v1/election-cycles/find-by-coverage/",
            {
                "start_date": "not-a-date",
                "end_date": "2024-06-30",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_find_by_coverage_start_date_after_end_date(self):
        response = self.client.get(
            "/api/v1/election-cycles/find-by-coverage/",
            {
                "start_date": "2024-07-01",
                "end_date": "2024-06-30",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["error"],
            "start_date must be less than or equal to end_date.",
        )

    def test_find_by_coverage_no_containing_cycle(self):
        response = self.client.get(
            "/api/v1/election-cycles/find-by-coverage/",
            {
                "start_date": "2022-01-01",
                "end_date": "2025-12-31",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"needs_cycle": True, "needs_next_cycle": False})

    def test_find_by_coverage_returns_next_cycle_when_both_cover_period(self):
        next_cycle = ElectionCycle.objects.create(
            committee_account=self.committee,
            office=ElectionCycle.Office.HOUSE,
            election_type=ElectionCycle.ElectionType.GENERAL,
            election_year="2026",
            start_date="2025-01-01",
            end_date="2026-12-31",
        )

        response = self.client.get(
            "/api/v1/election-cycles/find-by-coverage/",
            {
                "start_date": "2024-06-01",
                "end_date": "2025-06-30",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["needs_cycle"])
        self.assertFalse(response.data["needs_next_cycle"])
        self.assertEqual(
            response.data["election_cycle"]["id"],
            str(self.cycle_1.id),
        )
        self.assertEqual(
            response.data["next_election_cycle"]["id"],
            str(next_cycle.id),
        )

    def test_find_by_coverage_needs_next_cycle_when_no_next_cycle_exists(self):
        response = self.client.get(
            "/api/v1/election-cycles/find-by-coverage/",
            {
                "start_date": "2024-06-01",
                "end_date": "2025-06-30",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["needs_cycle"])
        self.assertTrue(response.data["needs_next_cycle"])
        self.assertEqual(
            response.data["election_cycle"]["id"],
            str(self.cycle_1.id),
        )
        self.assertNotIn("next_election_cycle", response.data)

    def test_find_by_coverage_needs_next_cycle_when_end_date_is_in_gap(self):
        ElectionCycle.objects.create(
            committee_account=self.committee,
            office=ElectionCycle.Office.HOUSE,
            election_type=ElectionCycle.ElectionType.GENERAL,
            election_year="2026",
            start_date="2025-06-01",
            end_date="2026-12-31",
        )

        response = self.client.get(
            "/api/v1/election-cycles/find-by-coverage/",
            {
                "start_date": "2024-06-01",
                "end_date": "2025-03-31",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["needs_cycle"])
        self.assertTrue(response.data["needs_next_cycle"])
        self.assertNotIn("next_election_cycle", response.data)

    def test_find_by_coverage_needs_next_cycle_when_end_exceeds_next_cycle(self):
        next_cycle = ElectionCycle.objects.create(
            committee_account=self.committee,
            office=ElectionCycle.Office.HOUSE,
            election_type=ElectionCycle.ElectionType.GENERAL,
            election_year="2026",
            start_date="2025-01-01",
            end_date="2025-12-31",
        )

        response = self.client.get(
            "/api/v1/election-cycles/find-by-coverage/",
            {
                "start_date": "2024-06-01",
                "end_date": "2026-06-30",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["needs_next_cycle"])
        self.assertEqual(
            response.data["election_cycle"]["id"],
            str(self.cycle_1.id),
        )
        self.assertNotIn("next_election_cycle", response.data)
        self.assertNotEqual(str(next_cycle.id), response.data["election_cycle"]["id"])

    def test_find_by_coverage_does_not_return_other_committee_cycle(self):
        other_committee = CommitteeAccount.objects.create(committee_id="C00000001")
        ElectionCycle.objects.create(
            committee_account=other_committee,
            office=ElectionCycle.Office.SENATE,
            election_type=ElectionCycle.ElectionType.GENERAL,
            election_year="2026",
            start_date="2025-01-01",
            end_date="2026-12-31",
        )

        response = self.client.get(
            "/api/v1/election-cycles/find-by-coverage/",
            {
                "start_date": "2025-06-01",
                "end_date": "2026-06-30",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"needs_cycle": True, "needs_next_cycle": False})
