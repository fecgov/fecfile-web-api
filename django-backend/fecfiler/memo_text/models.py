from fecfiler.soft_delete.models import SoftDeleteModel
from fecfiler.committee_accounts.models import CommitteeOwnedModel
from fecfiler.f3x_summaries.models import ReportMixin
from django.db import models


class MemoText(SoftDeleteModel, CommitteeOwnedModel, ReportMixin):
    rec_type = models.TextField(null=True, blank=True)
    filer_committee_id_number = models.TextField(null=True, blank=True)
    transaction_id_number = models.TextField(null=True, blank=True)
    back_reference_tran_id_number = models.TextField(null=True, blank=True)
    back_reference_sched_form_name = models.TextField(null=True, blank=True)
    text4000 = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "memo_text"
