from django.db import models
from django.core.validators import RegexValidator
from fecfiler.soft_delete.models import SoftDeleteModel

COMMITTEE_ID_REGEX = RegexValidator(r'^C[0-9]{8}$',
                                    'invalid committee id format')

class CommitteeAccount(SoftDeleteModel):
    committee_id = models.CharField(max_length=9, unique=True,
                                    validators=[COMMITTEE_ID_REGEX])
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "committee_accounts"

    def __str__(self):
        return self.committee_id