import uuid
from django.db import models
import structlog

logger = structlog.get_logger(__name__)


class Form1M(models.Model):
    """Generated model from json schema"""

    id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        primary_key=True,
        serialize=False,
        unique=True,
    )

    committee_name = models.TextField(null=True, blank=True)
    street_1 = models.TextField(null=True, blank=True)
    street_2 = models.TextField(null=True, blank=True)
    city = models.TextField(null=True, blank=True)
    state = models.TextField(null=True, blank=True)
    zip = models.TextField(null=True, blank=True)
    committee_type = models.CharField(max_length=1, null=True, blank=True)

    contact_affiliated = models.ForeignKey(
        "contacts.Contact",
        on_delete=models.CASCADE,
        related_name="contact_affiliated_transaction_set",
        null=True,
    )
    contact_candidate_I = models.ForeignKey(  # noqa: N815
        "contacts.Contact",
        on_delete=models.CASCADE,
        related_name="contact_candidate_I_transaction_set",
        null=True,
    )
    contact_candidate_II = models.ForeignKey(  # noqa: N815
        "contacts.Contact",
        on_delete=models.CASCADE,
        related_name="contact_candidate_II_transaction_set",
        null=True,
    )
    contact_candidate_III = models.ForeignKey(  # noqa: N815
        "contacts.Contact",
        on_delete=models.CASCADE,
        related_name="contact_candidate_III_transaction_set",
        null=True,
    )
    contact_candidate_IV = models.ForeignKey(  # noqa: N815
        "contacts.Contact",
        on_delete=models.CASCADE,
        related_name="contact_candidate_IV_transaction_set",
        null=True,
    )
    contact_candidate_V = models.ForeignKey(  # noqa: N815
        "contacts.Contact",
        on_delete=models.CASCADE,
        related_name="contact_candidate_V_transaction_set",
        null=True,
    )

    affiliated_date_form_f1_filed = models.DateField(null=True, blank=True)
    I_date_of_contribution = models.DateField(null=True, blank=True)
    II_date_of_contribution = models.DateField(null=True, blank=True)
    III_date_of_contribution = models.DateField(null=True, blank=True)
    IV_date_of_contribution = models.DateField(null=True, blank=True)
    V_date_of_contribution = models.DateField(null=True, blank=True)
    date_of_original_registration = models.DateField(null=True, blank=True)
    date_of_51st_contributor = models.DateField(null=True, blank=True)
    date_committee_met_requirements = models.DateField(null=True, blank=True)

    class Meta:
        app_label = "reports"
