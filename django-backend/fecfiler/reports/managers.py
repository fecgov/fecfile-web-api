from fecfiler.soft_delete.managers import SoftDeleteManager
from django.db.models import (
    Case,
    When,
    Value,
)
from enum import Enum

"""Manager to deterimine fields that are used the same way across reports,
but are called different names"""


class ReportManager(SoftDeleteManager):
    def get_queryset(self):
        queryset = (
            super()
            .get_queryset()
            .annotate(
                report_type=Case(
                    When(report_f3x__isnull=False, then=ReportType.F3X.value)
                ),
            )
        )
        return queryset


class ReportType(Enum):
    F3X = Value("F3X")
    F24 = Value("F24")
