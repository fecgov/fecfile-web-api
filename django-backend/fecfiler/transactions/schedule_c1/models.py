from django.db import models
import uuid


class ScheduleC1(models.Model):
    id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        primary_key=True,
        serialize=False,
        unique=True,
    )
    lender_organization_name = models.TextField(null=True, blank=True)
    lender_street_1 = models.TextField(null=True, blank=True)
    lender_street_2 = models.TextField(null=True, blank=True)
    lender_city = models.TextField(null=True, blank=True)
    lender_state = models.TextField(null=True, blank=True)
    lender_zip = models.TextField(null=True, blank=True)
    loan_amount = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    loan_interest_rate = models.TextField(null=True, blank=True)
    loan_incurred_date = models.DateField(null=True, blank=True)
    loan_due_date = models.TextField(null=True, blank=True)
    loan_restructured = models.BooleanField(null=True, blank=True, default=False)
    loan_originally_incurred_date = models.DateField(null=True, blank=True)
    credit_amount_this_draw = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    total_balance = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    others_liable = models.BooleanField(null=True, blank=True, default=False)
    collateral = models.BooleanField(null=True, blank=True, default=False)
    desc_collateral = models.TextField(null=True, blank=True)
    collateral_value_amount = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    perfected_interest = models.BooleanField(null=True, blank=True, default=False)
    future_income = models.BooleanField(null=True, blank=True, default=False)
    desc_specification_of_the_above = models.TextField(null=True, blank=True)
    estimated_value = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    depository_account_established_date = models.DateField(null=True, blank=True)
    ind_name_account_location = models.TextField(null=True, blank=True)
    account_street_1 = models.TextField(null=True, blank=True)
    account_street_2 = models.TextField(null=True, blank=True)
    account_city = models.TextField(null=True, blank=True)
    account_state = models.TextField(null=True, blank=True)
    account_zip = models.TextField(null=True, blank=True)
    dep_acct_auth_date_presidential = models.DateField(null=True, blank=True)
    basis_of_loan_description = models.TextField(null=True, blank=True)
    treasurer_last_name = models.TextField(null=True, blank=True)
    treasurer_first_name = models.TextField(null=True, blank=True)
    treasurer_middle_name = models.TextField(null=True, blank=True)
    treasurer_prefix = models.TextField(null=True, blank=True)
    treasurer_suffix = models.TextField(null=True, blank=True)
    treasurer_date_signed = models.DateField(null=True, blank=True)
    authorized_last_name = models.TextField(null=True, blank=True)
    authorized_first_name = models.TextField(null=True, blank=True)
    authorized_middle_name = models.TextField(null=True, blank=True)
    authorized_prefix = models.TextField(null=True, blank=True)
    authorized_suffix = models.TextField(null=True, blank=True)
    authorized_title = models.TextField(null=True, blank=True)
    authorized_date_signed = models.DateField(null=True, blank=True)

    # The line_of_credit field is strictly to save state for a front-end radio
    # button and is not part of the C1 spec
    line_of_credit = models.BooleanField(null=True, blank=True, default=False)

    def get_date(self):
        return self.loan_incurred_date

    def update_with_contact(self, contact):
        self.lender_organization_name = contact.name
        self.lender_street_1 = contact.street_1
        self.lender_street_2 = contact.street_2
        self.lender_city = contact.city
        self.lender_state = contact.state
        self.lender_zip = contact.zip
        self.save()

    class Meta:
        app_label = "transactions"
