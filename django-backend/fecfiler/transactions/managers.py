from fecfiler.soft_delete.managers import SoftDeleteManager
from django.db.models.functions import Coalesce

"""Manager to deterimine fields that are used the same way across transactions,
but are called different names"""


class TransactionManager(SoftDeleteManager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .annotate(action_date=Coalesce("schedule_a__contribution_date", None))
        )
