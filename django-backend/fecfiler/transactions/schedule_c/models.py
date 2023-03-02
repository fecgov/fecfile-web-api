from django.db import models
import uuid


class ScheduleC(models.Model):
    id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        primary_key=True,
        serialize=False,
        unique=True,
    )
    receipt_line_number = models.TextField(null=True, blank=True)
    lender_organization_name = models.TextField(null=True, blank=True)
    lender_last_name = models.TextField(null=True, blank=True)
    lender_first_name = models.TextField(null=True, blank=True)
    lender_middle_name = models.TextField(null=True, blank=True)
    lender_prefix = models.TextField(null=True, blank=True)
    lender_suffix = models.TextField(null=True, blank=True)
    lender_street_1 = models.TextField(null=True, blank=True)
    lender_street_2 = models.TextField(null=True, blank=True)
    lender_city = models.TextField(null=True, blank=True)
    lender_state = models.TextField(null=True, blank=True)
    lender_zip = models.TextField(null=True, blank=True)
    election_code = models.TextField(null=True, blank=True)
    election_other_description = models.TextField(null=True, blank=True)
    loan_amount = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    loan_payment_to_date = models.TextField(null=True, blank=True)
    loan_balance = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    loan_incurred_date = models.DateField(null=True, blank=True)
    loan_due_date = models.DateField(null=True, blank=True)
    loan_interest_rate = models.DecimalField(
        null=True, blank=True, max_digits=14, decimal_places=14
    )
    secured = models.BooleanField(null=True, blank=True, default=False)
    personal_funds = models.BooleanField(null=True, blank=True, default=False)
    lender_committee_id_number = models.TextField(null=True, blank=True)
    lender_candidate_id_number = models.TextField(null=True, blank=True)
    lender_candidate_last_name = models.TextField(null=True, blank=True)
    lender_candidate_first_name = models.TextField(null=True, blank=True)
    lender_candidate_middle_name = models.TextField(null=True, blank=True)
    lender_candidate_prefix = models.TextField(null=True, blank=True)
    lender_candidate_suffix = models.TextField(null=True, blank=True)
    lender_candidate_office = models.TextField(null=True, blank=True)
    lender_candidate_state = models.TextField(null=True, blank=True)
    lender_candidate_district = models.TextField(null=True, blank=True)
    memo_text_description = models.TextField(null=True, blank=True)

    class Meta:
        app_label = "transactions"
