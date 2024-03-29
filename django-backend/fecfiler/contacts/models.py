import uuid
from django.db import models
from fecfiler.soft_delete.models import SoftDeleteModel
from fecfiler.committee_accounts.models import CommitteeOwnedModel


class Contact(SoftDeleteModel, CommitteeOwnedModel):
    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)

    class ContactType(models.TextChoices):
        COMMITTEE = "COM"
        ORGANIZATION = "ORG"
        INDIVIDUAL = "IND"
        CANDIDATE = "CAN"

    class CandidateOffice(models.TextChoices):
        HOUSE = "H"
        SENATE = "S"
        PRESIDENTIAL = "P"

    """Generated model from json schema"""
    type = models.CharField(
        choices=ContactType.choices, max_length=3, null=True, blank=False
    )
    candidate_id = models.TextField(null=True, blank=True)
    committee_id = models.TextField(null=True, blank=True)
    #: str: Name of contact when multi-part name is not used
    name = models.TextField(null=True, blank=True)
    last_name = models.TextField(null=True, blank=True)
    first_name = models.TextField(null=True, blank=True)
    middle_name = models.TextField(null=True, blank=True)
    prefix = models.TextField(null=True, blank=True)
    suffix = models.TextField(null=True, blank=True)
    street_1 = models.TextField(null=True, blank=False)
    street_2 = models.TextField(null=True, blank=True)
    city = models.TextField(null=True, blank=False)
    state = models.TextField(null=True, blank=False)
    zip = models.TextField(null=True, blank=False)
    employer = models.TextField(null=True, blank=True)
    occupation = models.TextField(null=True, blank=True)
    candidate_office = models.CharField(
        choices=CandidateOffice.choices, max_length=1, null=True, blank=True
    )
    candidate_state = models.TextField(null=True, blank=True)
    candidate_district = models.TextField(null=True, blank=True)
    telephone = models.TextField(null=True, blank=True)
    country = models.TextField(null=True, blank=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "contacts"

    def __str__(self):
        if self.type in [Contact.ContactType.CANDIDATE, Contact.ContactType.INDIVIDUAL]:
            return f"{self.last_name}, {self.first_name}"
        else:
            return self.name
