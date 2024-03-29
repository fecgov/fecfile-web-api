from fecfiler.soft_delete.managers import SoftDeleteManager
from django.db.models import Case, When, Value, OuterRef, Exists
from enum import Enum

"""Manager to deterimine fields that are used the same way across reports,
but are called different names"""


class ReportManager(SoftDeleteManager):
    def get_queryset(self):
        older_f3x = (
            super()
            .get_queryset()
            .filter(
                form_3x__isnull=False,
                committee_account_id=OuterRef("committee_account_id"),
                created__lt=OuterRef("created"),
            )
        )
        queryset = (
            super()
            .get_queryset()
            .annotate(
                report_type=Case(
                    When(form_3x__isnull=False, then=ReportType.F3X.value),
                    When(form_24__isnull=False, then=ReportType.F24.value),
                    When(form_99__isnull=False, then=ReportType.F99.value),
                    When(form_1m__isnull=False, then=ReportType.F1M.value),
                ),
                is_first=~Exists(older_f3x),
            )
        )
        return queryset


class ReportType(Enum):
    F3X = Value("F3X")
    F24 = Value("F24")
    F99 = Value("F99")
    F1M = Value("F1M")
