from rest_framework import filters
from django.db.models import Case, Value, When
from fecfiler.committee_accounts.views import CommitteeOwnedViewSet
from .models import F3XSummary, ReportCodeLabels
from .serializers import F3XSummarySerializer


class F3XSummaryViewSet(CommitteeOwnedViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.

    Note that this ViewSet inherits from CommitteeOwnedViewSet
    The queryset will be further limited by the user's committee
    in CommitteeOwnedViewSet's implementation of get_queryset()
    """

    report_code_labels = ReportCodeLabels()
    for label in report_code_labels.labels:
        ""
    

    """
    queryset = F3XSummary.objects.alias(report_code_label=Case(
        When(report_code='Q1', then=Value('APRIL 15 (Q1)')),
        When(report_code='Q2', then=Value('JULY 15 (Q2)')),
        When(report_code='Q3', then=Value('OCTOBER 15 (Q3)')),
        When(report_code='YE', then=Value('JANUARY 31 (YE)')),
        When(report_code='TER', then=Value('TERMINATION (TER)')),
        When(report_code='MY', then=Value('JANUARY 31 (MY)')),
        When(report_code='12G', then=Value('GENERAL (12G)')),
        When(report_code='12P', then=Value('PRIMARY (12P)')),
        When(report_code='12R', then=Value('RUNOFF (12R)')),
        When(report_code='12S', then=Value('SPECIAL (12S)')),
        When(report_code='12C', then=Value('CONVENTION (12C)')),
        When(report_code='30G', then=Value('GENERAL (30G)')),
        When(report_code='30R', then=Value('RUNOFF (30R)')),
        When(report_code='30S', then=Value('SPECIAL (30S)')),
        When(report_code='M2', then=Value('FEBRUARY 20 (M2)')),
        When(report_code='M3', then=Value('MARCH 20 (M3)')),
        When(report_code='M4', then=Value('APRIL 20 (M4)')),
        When(report_code='M5', then=Value('MAY 20 (M5)')),
        When(report_code='M6', then=Value('JUNE 20 (M6)')),
        When(report_code='M7', then=Value('JULY 20 (M7)')),
        When(report_code='M8', then=Value('AUGUST 20 (M8)')),
        When(report_code='M9', then=Value('SEPTEMBER 20 (M9)')),
        When(report_code='M10', then=Value('OCTOBER 20 (M10)')),
        When(report_code='M11', then=Value('NOVEMBER 20 (M11)')),
        When(report_code='M12', then=Value('DECEMBER 20 (M12)')),
        default=Value('_NOT_FOUND_'),
    )).all()
    """

    serializer_class = F3XSummarySerializer
    permission_classes = []
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['form_type', 'report_code_label', 'coverage_through_date']
    ordering = ['form_type']
