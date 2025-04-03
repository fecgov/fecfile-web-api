from django.db.models import Case, When, Value, Manager, Q, CharField
from enum import Enum

"""Manager to deterimine fields that are used the same way across reports,
but are called different names"""


def get_status_mapping():
    """returns Django Case that determines report status based on upload submission"""
    from fecfiler.web_services.models import FECSubmissionState, FECStatus

    # there is an upload record, meaning the user submitted the report, but it could
    # be at any stage in the process
    upload_exists = Q(upload_submission__isnull=False)
    # if the `fec_status` is ACCEPTED, efo has accepted the submission
    success = Q(upload_submission__fec_status=FECStatus.ACCEPTED)
    # if the `fecfile_task_state` is FAILED, there was an error in one of our tasks
    # if the `fec_status` is REJECTED, efo deemed the submission to not be successful
    failed = Q(upload_submission__fecfile_task_state=FECSubmissionState.FAILED) | Q(
        upload_submission__fec_status=FECStatus.REJECTED
    )

    return Case(
        # the report was submitted and efo returned a "success"
        When(success, then=Value("Submission success")),
        # the submission failed either on our side or efo's side
        When(failed, then=Value("Submission failure")),
        # the report has been sent to efo, we are waiting on a response
        When(upload_exists, then=Value("Submission pending")),
        # the report is in progress because there is no
        # upload_submission associated with it
        default=Value("In progress"),
        output_field=CharField(),
    )


class ReportManager(Manager):
    def get_queryset(self):
        queryset = (
            super()
            .get_queryset()
            .annotate(
                report_type=Case(
                    When(form_3__isnull=False, then=ReportType.F3.value),
                    When(form_3x__isnull=False, then=ReportType.F3X.value),
                    When(form_24__isnull=False, then=ReportType.F24.value),
                    When(form_99__isnull=False, then=ReportType.F99.value),
                    When(form_1m__isnull=False, then=ReportType.F1M.value),
                ),
                # report status must be in queryset because it is sorted on
                report_status=get_status_mapping(),
            )
        )
        return queryset


class ReportType(Enum):
    F3 = Value("F3")
    F3X = Value("F3X")
    F24 = Value("F24")
    F99 = Value("F99")
    F1M = Value("F1M")
