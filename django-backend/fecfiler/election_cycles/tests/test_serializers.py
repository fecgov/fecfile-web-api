import uuid

from django.test import TestCase
from rest_framework.request import HttpRequest, Request
from django.db.models import Exists, OuterRef
from fecfiler.reports.form_3.models import Form3
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.user.models import User
from ..models import ElectionCycle
from ..serializers import ElectionCycleSerializer


class ElectionCycleSerializerTestCase(TestCase):
    def get_annotated_election_cycle(self, instance):
        return ElectionCycle.objects.annotate(
            has_form3=Exists(Form3.objects.filter(election_cycle_id=OuterRef("pk")))
        ).get(pk=instance.pk)

    def setUp(self):
        self.committee = CommitteeAccount.objects.create(committee_id="C00000000")
        self.user = User.objects.create(
            email="test@fec.gov",
            username="gov",
        )

        self.valid_election_cycle = {
            "office": "House",
            "election_type": "General",
            "election_year": "2024",
            "start_date": "2023-01-01",
            "end_date": "2024-12-31",
        }

        self.invalid_election_cycle = {
            "office": "GOVERNOR",
            "election_type": "General",
            "election_year": "24",
            "start_date": "2023-01-01",
            "end_date": "2024-12-31",
        }

        self.mock_request = Request(HttpRequest())
        self.mock_request.user = self.user
        self.mock_request.session = {
            "committee_uuid": str(self.committee.id),
            "committee_id": str(self.committee.committee_id),
        }

    def test_serializer_validate(self):
        valid_serializer = ElectionCycleSerializer(
            data=self.valid_election_cycle,
            context={"request": self.mock_request},
        )
        self.assertTrue(valid_serializer.is_valid(raise_exception=True))

        invalid_serializer = ElectionCycleSerializer(
            data=self.invalid_election_cycle,
            context={"request": self.mock_request},
        )
        self.assertFalse(invalid_serializer.is_valid())
        self.assertIn("office", invalid_serializer.errors)
        self.assertIn("election_year", invalid_serializer.errors)

    def test_serialize_existing_instance(self):
        instance = ElectionCycle.objects.create(
            committee_account=self.committee,
            **self.valid_election_cycle,
        )
        instance = self.get_annotated_election_cycle(instance)

        serializer = ElectionCycleSerializer(
            instance,
            context={"request": self.mock_request},
        )

        self.assertEqual(serializer.data["office"], "House")
        self.assertEqual(serializer.data["election_type"], "General")
        self.assertEqual(serializer.data["election_year"], "2024")
        self.assertIn("has_form3", serializer.data)
        self.assertFalse(serializer.data["has_form3"])

    def test_has_form3_is_read_only(self):
        data = {
            **self.valid_election_cycle,
            "has_form3": True,
        }

        serializer = ElectionCycleSerializer(
            data=data,
            context={"request": self.mock_request},
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertNotIn("has_form3", serializer.validated_data)

        instance = serializer.save()

        instance = self.get_annotated_election_cycle(instance)
        self.assertFalse(instance.has_form3)

    def test_read_only_id(self):
        data_with_id = {
            **self.valid_election_cycle,
            "id": str(uuid.uuid4()),
        }

        serializer = ElectionCycleSerializer(
            data=data_with_id,
            context={"request": self.mock_request},
        )

        self.assertTrue(serializer.is_valid(raise_exception=True))
        instance = serializer.save()

        self.assertNotEqual(str(instance.id), data_with_id["id"])
