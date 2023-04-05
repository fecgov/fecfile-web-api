from django.db import models
import uuid


class ScheduleB(models.Model):
    id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        primary_key=True,
        serialize=False,
        unique=True,
    )
    payee_organization_name = models.TextField(null=True, blank=True)
    payee_last_name = models.TextField(null=True, blank=True)
    payee_first_name = models.TextField(null=True, blank=True)
    payee_middle_name = models.TextField(null=True, blank=True)
    payee_prefix = models.TextField(null=True, blank=True)
    payee_suffix = models.TextField(null=True, blank=True)
    payee_street_1 = models.TextField(null=True, blank=True)
    payee_street_2 = models.TextField(null=True, blank=True)
    payee_city = models.TextField(null=True, blank=True)
    payee_state = models.TextField(null=True, blank=True)
    payee_zip = models.TextField(null=True, blank=True)

    expenditure_date = models.DateField(null=True, blank=True)
    expenditure_amount = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )

    expenditure_purpose_descrip = models.TextField(null=True, blank=True)

    election_code = models.TextField(null=True, blank=True)
    election_other_description = models.TextField(null=True, blank=True)
    conduit_name = models.TextField(null=True, blank=True)
    conduit_street_1 = models.TextField(null=True, blank=True)
    conduit_street_2 = models.TextField(null=True, blank=True)
    conduit_city = models.TextField(null=True, blank=True)
    conduit_state = models.TextField(null=True, blank=True)
    conduit_zip = models.TextField(null=True, blank=True)

    category_code = models.TextField(null=True, blank=True)

    beneficiary_committee_fec_id = models.TextField(null=True, blank=True)
    beneficiary_committee_name = models.TextField(null=True, blank=True)
    beneficiary_candidate_fec_id = models.TextField(null=True, blank=True)
    beneficiary_candidate_last_name = models.TextField(null=True, blank=True)
    beneficiary_candidate_first_name = models.TextField(null=True, blank=True)
    beneficiary_candidate_middle_name = models.TextField(null=True, blank=True)
    beneficiary_candidate_prefix = models.TextField(null=True, blank=True)
    beneficiary_candidate_suffix = models.TextField(null=True, blank=True)
    beneficiary_candidate_office = models.TextField(null=True, blank=True)
    beneficiary_candidate_state = models.TextField(null=True, blank=True)
    beneficiary_candidate_district = models.TextField(null=True, blank=True)

    memo_text_description = models.TextField(null=True, blank=True)
    reference_to_si_or_sl_system_code_that_identifies_the_account = models.TextField(
        null=True, blank=True
    )

    class Meta:
        app_label = "transactions"
