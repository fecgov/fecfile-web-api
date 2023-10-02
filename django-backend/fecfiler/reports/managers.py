from fecfiler.soft_delete.managers import SoftDeleteManager
from django.db.models.functions import Coalesce, Concat
from django.db.models import (
    Case,
    When,
    Value,
)
from decimal import Decimal
from enum import Enum

"""Manager to deterimine fields that are used the same way across transactions,
but are called different names"""


class ReportManager(SoftDeleteManager):
    def get_queryset(self):
        queryset = (
            super()
            .get_queryset()
            .annotate(
                report=Case(
                    When(f3x_report__isnull=False, then=ReportEnum.F3X.value),
                ),
            )
        )
        return queryset.order_by("created")


class ReportEnum(Enum):
    F3X = Value("F3X")
