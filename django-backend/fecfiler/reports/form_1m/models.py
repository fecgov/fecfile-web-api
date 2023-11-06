import uuid
from django.db import models
import logging


logger = logging.getLogger(__name__)


class Form1M(models.Model):
    """Generated model from json schema"""

    id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        primary_key=True,
        serialize=False,
        unique=True,
    )

    street_1 = models.TextField(null=True, blank=True)
    street_2 = models.TextField(null=True, blank=True)
    city = models.TextField(null=True, blank=True)
    state = models.TextField(null=True, blank=True)
    zip = models.TextField(null=True, blank=True)
    committee_type = models.CharField(max_length=1, null=True, blank=True)

    affiliated_date_form_f1_filed = models.DateField(null=True, blank=True)
    affiliated_date_committee_fec_id = models.DateField(null=True, blank=True)
    affiliated_committee_name = models.TextField(null=True, blank=True)

    I_candidate_id_number = models.TextField(null=True, blank=True)
    I_candidate_last_name = models.TextField(null=True, blank=True)
    I_candidate_first_name = models.TextField(null=True, blank=True)
    I_candidate_middle_name = models.TextField(null=True, blank=True)
    I_candidate_prefix = models.TextField(null=True, blank=True)
    I_candidate_suffix = models.TextField(null=True, blank=True)
    I_candidate_office = models.CharField(max_length=1, null=True, blank=True)
    I_candidate_state = models.TextField(null=True, blank=True)
    I_candidate_district = models.TextField(null=True, blank=True)
    I_date_of_contribution = models.DateField(null=True, blank=True)

    II_candidate_id_number = models.TextField(null=True, blank=True)
    II_candidate_last_name = models.TextField(null=True, blank=True)
    II_candidate_first_name = models.TextField(null=True, blank=True)
    II_candidate_middle_name = models.TextField(null=True, blank=True)
    II_candidate_prefix = models.TextField(null=True, blank=True)
    II_candidate_suffix = models.TextField(null=True, blank=True)
    II_candidate_office = models.CharField(max_length=1, null=True, blank=True)
    II_candidate_state = models.TextField(null=True, blank=True)
    II_candidate_district = models.TextField(null=True, blank=True)
    II_date_of_contribution = models.DateField(null=True, blank=True)

    III_candidate_id_number = models.TextField(null=True, blank=True)
    III_candidate_last_name = models.TextField(null=True, blank=True)
    III_candidate_first_name = models.TextField(null=True, blank=True)
    III_candidate_middle_name = models.TextField(null=True, blank=True)
    III_candidate_prefix = models.TextField(null=True, blank=True)
    III_candidate_suffix = models.TextField(null=True, blank=True)
    III_candidate_office = models.CharField(max_length=1, null=True, blank=True)
    III_candidate_state = models.TextField(null=True, blank=True)
    III_candidate_district = models.TextField(null=True, blank=True)
    III_date_of_contribution = models.DateField(null=True, blank=True)

    IV_candidate_id_number = models.TextField(null=True, blank=True)
    IV_candidate_last_name = models.TextField(null=True, blank=True)
    IV_candidate_first_name = models.TextField(null=True, blank=True)
    IV_candidate_middle_name = models.TextField(null=True, blank=True)
    IV_candidate_prefix = models.TextField(null=True, blank=True)
    IV_candidate_suffix = models.TextField(null=True, blank=True)
    IV_candidate_office = models.CharField(max_length=1, null=True, blank=True)
    IV_candidate_state = models.TextField(null=True, blank=True)
    IV_candidate_district = models.TextField(null=True, blank=True)
    IV_date_of_contribution = models.DateField(null=True, blank=True)

    V_candidate_id_number = models.TextField(null=True, blank=True)
    V_candidate_last_name = models.TextField(null=True, blank=True)
    V_candidate_first_name = models.TextField(null=True, blank=True)
    V_candidate_middle_name = models.TextField(null=True, blank=True)
    V_candidate_prefix = models.TextField(null=True, blank=True)
    V_candidate_suffix = models.TextField(null=True, blank=True)
    V_candidate_office = models.CharField(max_length=1, null=True, blank=True)
    V_candidate_state = models.TextField(null=True, blank=True)
    V_candidate_district = models.TextField(null=True, blank=True)
    V_date_of_contribution = models.DateField(null=True, blank=True)

    class Meta:
        app_label = "reports"
