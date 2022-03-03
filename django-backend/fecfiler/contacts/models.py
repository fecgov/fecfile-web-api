from django.db import models
from fecfiler.core.models import SoftDeleteModel
from fecfile_validate import validate


class Contact(SoftDeleteModel):

    class ContactType(models.TextChoices):
        COMMITTEE = "Committee",
        ORGANIZATION = "Organization",
        INDIVIDUAL = "Individual",
        CANDIDATE = "Candidate"

    class CandidateOffice(models.TextChoices):
        HOUSE = "House",
        SENATE = "Senate",
        PRESIDENTIAL = "Presidential"

    """Generated model from json schema"""
    type = models.CharField(
        choices=ContactType.choices, max_length=255, null=False, blank=False
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
    street_1 = models.TextField(null=False, blank=False)
    street_2 = models.TextField(null=True, blank=True)
    city = models.TextField(null=False, blank=False)
    state = models.TextField(null=False, blank=False)
    zip = models.TextField(null=False, blank=False)
    employer = models.TextField(null=True, blank=True)
    occupation = models.TextField(null=True, blank=True)
    candidate_office = models.CharField(
        choices=CandidateOffice.choices, max_length=255, null=True, blank=True
    )
    candidate_state = models.TextField(null=True, blank=True)
    candidate_district = models.TextField(null=True, blank=True)
    telephone = models.TextField(null=True, blank=True)
    country = models.TextField(null=False, blank=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'contacts'

    def __str__(self):
        if self.type in [Contact.ContactType.CANDIDATE, Contact.ContactType.INDIVIDUAL]:
            return f'{self.last_name}, {self.first_name}'
        else:
            return self.name

    def fecfile_validate():
        schema = f"Contact_{self.type}"
        return validate.validate(schema, self)
