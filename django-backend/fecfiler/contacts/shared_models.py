from django.db import models


class ContactType(models.TextChoices):
    COMMITTEE = "COM"
    ORGANIZATION = "ORG"
    INDIVIDUAL = "IND"
    CANDIDATE = "CAN"


class CandidateOffice(models.TextChoices):
    HOUSE = "H"
    SENATE = "S"
    PRESIDENTIAL = "P"
