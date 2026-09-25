from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.user.models import User
from ..models import ElectionCycle


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
        self.assertEqual(response.data["results"][0]["id"], str(self.cycle_1.id))

    def test_retrieve_election_cycle(self):
        response = self.client.get(f"/api/v1/election-cycles/{self.cycle_1.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["office"], "House")
        self.assertEqual(response.data["election_year"], "2024")

    def test_create_election_cycle(self):
        response = self.client.post(
            "/api/v1/election-cycles/",
            data=self.valid_payload,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ElectionCycle.objects.count(), 2)

    def test_update_election_cycle(self):
        update_data = {**self.valid_payload, "office": "Presidential"}
        response = self.client.put(
            f"/api/v1/election-cycles/{self.cycle_1.id}/",
            data=update_data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.cycle_1.refresh_from_db()
        self.assertEqual(self.cycle_1.office, "Presidential")

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
