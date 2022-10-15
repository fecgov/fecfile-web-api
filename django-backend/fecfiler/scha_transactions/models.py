from django.db import models
from .managers import SchATransactionManager
from fecfiler.soft_delete.models import SoftDeleteModel
from fecfiler.committee_accounts.models import CommitteeOwnedModel
from fecfiler.f3x_summaries.models import ReportMixin
import uuid
import logging


logger = logging.getLogger(__name__)


class SchATransaction(SoftDeleteModel, CommitteeOwnedModel, ReportMixin):
    """Manager Definition"""

    objects = SchATransactionManager()
    """Generated model from json schema"""

    id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        primary_key=True,
        serialize=False,
        unique=True,
    )

    form_type = models.TextField(null=True, blank=True)
    # TODO get rid of this field.  It is redundant with the related Committee_Account
    filer_committee_id_number = models.TextField(null=True, blank=True)
    transaction_id = models.TextField(null=True, blank=False, max_length=20)
    # TODO get rid of this field.  It is redundant with the related Parent Transaction
    back_reference_tran_id_number = models.TextField(
        null=True, blank=True, max_length=20
    )
    # TODO get rid of this field.  It is redundant with the related Parent Transaction
    back_reference_sched_name = models.TextField(null=True, blank=True)
    entity_type = models.TextField(null=True, blank=True)
    contributor_organization_name = models.TextField(null=True, blank=True)
    contributor_last_name = models.TextField(null=True, blank=True)
    contributor_first_name = models.TextField(null=True, blank=True)
    contributor_middle_name = models.TextField(null=True, blank=True)
    contributor_prefix = models.TextField(null=True, blank=True)
    contributor_suffix = models.TextField(null=True, blank=True)
    contributor_street_1 = models.TextField(null=True, blank=True)
    contributor_street_2 = models.TextField(null=True, blank=True)
    contributor_city = models.TextField(null=True, blank=True)
    contributor_state = models.TextField(null=True, blank=True)
    contributor_zip = models.TextField(null=True, blank=True)
    election_code = models.TextField(null=True, blank=True)
    election_other_description = models.TextField(null=True, blank=True)
    contribution_date = models.DateField(null=True, blank=True)
    contribution_amount = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    aggregation_group = models.TextField(null=True, blank=True)
    contribution_purpose_descrip = models.TextField(null=True, blank=True)
    contributor_employer = models.TextField(null=True, blank=True)
    contributor_occupation = models.TextField(null=True, blank=True)
    donor_committee_fec_id = models.TextField(null=True, blank=True)
    donor_committee_name = models.TextField(null=True, blank=True)
    donor_candidate_fec_id = models.TextField(null=True, blank=True)
    donor_candidate_last_name = models.TextField(null=True, blank=True)
    donor_candidate_first_name = models.TextField(null=True, blank=True)
    donor_candidate_middle_name = models.TextField(null=True, blank=True)
    donor_candidate_prefix = models.TextField(null=True, blank=True)
    donor_candidate_suffix = models.TextField(null=True, blank=True)
    donor_candidate_office = models.TextField(null=True, blank=True)
    donor_candidate_state = models.TextField(null=True, blank=True)
    donor_candidate_district = models.TextField(null=True, blank=True)
    conduit_name = models.TextField(null=True, blank=True)
    conduit_street1 = models.TextField(null=True, blank=True)
    conduit_street2 = models.TextField(null=True, blank=True)
    conduit_city = models.TextField(null=True, blank=True)
    conduit_state = models.TextField(null=True, blank=True)
    conduit_zip = models.TextField(null=True, blank=True)
    memo_code = models.BooleanField(null=True, blank=True, default=False)
    memo_text_description = models.TextField(null=True, blank=True)
    reference_to_si_or_sl_system_code_that_identifies_the_account = models.TextField(
        null=True, blank=True
    )
    transaction_type_identifier = models.TextField(null=True, blank=True)
    parent_transaction = models.ForeignKey(
        "self", null=True, blank=True, default=None, on_delete=models.CASCADE
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    contact = models.ForeignKey("contacts.Contact", on_delete=models.CASCADE, null=True)

    class Meta:
        db_table = "scha_transactions"
        indexes = [models.Index(fields=["transaction_id"])]

    @staticmethod
    def get_virtual_field(field_name):
        virtual_fields = {
            "contribution_aggregate": models.DecimalField(
                max_digits=11, decimal_places=2
            )
        }
        return virtual_fields[field_name]

    # This is intended to be useable without instantiating a transaction object
    @staticmethod
    def check_for_uid_conflicts(uid):  # noqa
        return len(SchATransaction.objects.filter(transaction_id=uid)) > 0

    def generate_uid(self):
        unique_id = uuid.uuid4()
        hex_id = unique_id.hex.upper()
        # Take 20 characters from the end, skipping over the 20th char from the right,
        # which is the version number (uuid4 -> "4")
        return hex_id[-21] + hex_id[-19:]

    def generate_unique_transaction_id(self):
        unique_id = self.generate_uid()

        attempts = 0
        while SchATransaction.check_for_uid_conflicts(unique_id):
            unique_id = self.generate_uid()
            attempts += 1
            logger.info("Transaction unique ID generation: collision detected")
            if attempts > 5:
                logger.info("Unique ID generation failed: Over 5 conflicts in a row")
                return ""
        return unique_id

    def update_parent_related_values(self, parent):
        self.back_reference_tran_id_number = parent.transaction_id
        self.back_reference_sched_name = parent.form_type

    def save(self, *args, **kwargs):
        if not self.transaction_id:
            self.transaction_id = self.generate_unique_transaction_id()
        if not self.back_reference_tran_id_number and self.parent_transaction:
            self.update_parent_related_values(self.parent_transaction)

        super(SchATransaction, self).save(*args, **kwargs)
