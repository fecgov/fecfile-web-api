import logging

from django.contrib.postgres.fields import ArrayField
from django.db import models
import uuid

logger = logging.getLogger(__name__)


class MockCommitteeDetail(models.Model):
    id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        primary_key=True,
        serialize=False,
        unique=True,
    )
    affiliated_committee_name = models.TextField(null=True, blank=True)
    candidate_ids = ArrayField(models.TextField(), null=True, blank=True)
    city = models.TextField(null=True, blank=True)
    committee_id = models.TextField(unique=True)
    committee_type = models.TextField(null=True, blank=True)
    committee_type_full = models.TextField(null=True, blank=True)
    custodian_city = models.TextField(null=True, blank=True)
    custodian_name_1 = models.TextField(null=True, blank=True)
    custodian_name_2 = models.TextField(null=True, blank=True)
    custodian_name_full = models.TextField(null=True, blank=True)
    custodian_name_middle = models.TextField(null=True, blank=True)
    custodian_name_prefix = models.TextField(null=True, blank=True)
    custodian_name_suffix = models.TextField(null=True, blank=True)
    custodian_name_title = models.TextField(null=True, blank=True)
    custodian_phone = models.TextField(null=True, blank=True)
    custodian_state = models.TextField(null=True, blank=True)
    custodian_street_1 = models.TextField(null=True, blank=True)
    custodian_street_2 = models.TextField(null=True, blank=True)
    custodian_zip = models.TextField(null=True, blank=True)
    cycles = ArrayField(models.IntegerField(), null=True, blank=True)
    designation = models.TextField(null=True, blank=True)
    designation_full = models.TextField(null=True, blank=True)
    email = models.TextField(null=True, blank=True)
    filing_frequency = models.TextField(null=True, blank=True)
    first_f1_date = models.TextField(null=True, blank=True)
    first_file_date = models.TextField(null=True, blank=True)
    form_type = models.TextField(null=True, blank=True)
    last_f1_date = models.TextField(null=True, blank=True)
    last_file_date = models.TextField(null=True, blank=True)
    leadership_pac = models.TextField(null=True, blank=True)
    lobbyist_registrant_pac = models.TextField(null=True, blank=True)
    name = models.TextField(null=True, blank=True)
    organization_type = models.TextField(null=True, blank=True)
    organization_type_full = models.TextField(null=True, blank=True)
    party = models.TextField(null=True, blank=True)
    party_full = models.TextField(null=True, blank=True)
    party_type = models.TextField(null=True, blank=True)
    party_type_full = models.TextField(null=True, blank=True)
    sponsor_candidate_ids = models.TextField(null=True, blank=True)
    state = models.TextField(null=True, blank=True)
    state_full = models.TextField(null=True, blank=True)
    street_1 = models.TextField(null=True, blank=True)
    street_2 = models.TextField(null=True, blank=True)
    treasurer_city = models.TextField(null=True, blank=True)
    treasurer_name = models.TextField(null=True, blank=True)
    treasurer_name_1 = models.TextField(null=True, blank=True)
    treasurer_name_2 = models.TextField(null=True, blank=True)
    treasurer_name_middle = models.TextField(null=True, blank=True)
    treasurer_name_prefix = models.TextField(null=True, blank=True)
    treasurer_name_suffix = models.TextField(null=True, blank=True)
    treasurer_name_title = models.TextField(null=True, blank=True)
    treasurer_phone = models.TextField(null=True, blank=True)
    treasurer_state = models.TextField(null=True, blank=True)
    treasurer_street_1 = models.TextField(null=True, blank=True)
    treasurer_street_2 = models.TextField(null=True, blank=True)
    treasurer_zip = models.TextField(null=True, blank=True)
    website = models.TextField(null=True, blank=True)
    zip = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "mock_committee_detail"
