from uuid import UUID
from ..models import Report
from fecfiler.web_services.models import (
    DotFEC,
    UploadSubmission,
    WebPrintSubmission,
)
from fecfiler.contacts.models import Contact
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.transactions.models import Transaction
from fecfiler.memo_text.models import MemoText
from fecfiler.s3 import S3_SESSION
from fecfiler.settings import AWS_STORAGE_BUCKET_NAME
import re
import structlog

logger = structlog.get_logger(__name__)


def reset_submitting_report(id):
    report_uuid = UUID(id)

    # fetch upload_submission_id and delete associated upload record
    upload_submission_id = (
        Report.objects.filter(id=report_uuid)
        .values_list("upload_submission_id", flat=True)
        .first()
    )
    if upload_submission_id:
        UploadSubmission.objects.get(id=upload_submission_id).delete()

    # fetch webprint_submission_id and delete associated webprint record
    webprint_submission_id = (
        Report.objects.filter(id=report_uuid)
        .values_list("webprint_submission_id", flat=True)
        .first()
    )
    if webprint_submission_id:
        WebPrintSubmission.objects.get(id=webprint_submission_id).delete()

    # clear the dot_fec record if matching report_id found and delete from S3
    dot_fec_record = DotFEC.objects.filter(report_id=report_uuid).first()
    if dot_fec_record:
        if S3_SESSION is not None:
            file_name = dot_fec_record.file_name
            s3_object = S3_SESSION.Object(AWS_STORAGE_BUCKET_NAME, file_name)
            s3_object.delete()
            logger.info(f"Deleted dotfec file {file_name} from S3.")
        dot_fec_record.delete()

    Report.objects.filter(id=report_uuid).update(
        calculation_status=None,
        calculation_token=None,
        upload_submission_id=None,
        webprint_submission_id=None,
    )


def delete_committee_reports(committee_id, delete_contacts=False):
    if committee_id is None or len(committee_id) == 0:
        logger.error("No committee ID provided")
        return

    cid_regex = re.compile("^C[0-9]{8}$")
    if not cid_regex.match(str(committee_id)):
        logger.error(f'Invalid committee ID "{committee_id}"')
        return

    committee = CommitteeAccount.objects.filter(committee_id=committee_id).first()
    if committee is None:
        logger.error("No matching committee")
        return

    delete_all_reports(committee_id, log_method=logger.warn)

    # If delete-contacts flag is set, delete contacts as well
    if delete_contacts:
        logger.info("Deleting contacts associated with the committee...")
        delete_committee_contacts(committee_id)


def delete_all_reports(committee_id="C99999999", log_method=logger.warn):
    reports = Report.objects.filter(committee_account__committee_id=committee_id)
    transactions = Transaction.objects.filter(
        committee_account__committee_id=committee_id
    )

    report_count = reports.count()
    transaction_count = transactions.count()
    memo_count = MemoText.objects.filter(
        report__committee_account__committee_id=committee_id
    ).count()
    dot_fec_count = DotFEC.objects.filter(
        report__committee_account__committee_id=committee_id
    ).count()
    upload_submission_count = UploadSubmission.objects.filter(
        dot_fec__report__committee_account__committee_id=committee_id
    ).count()
    web_print_submission_count = WebPrintSubmission.objects.filter(
        dot_fec__report__committee_account__committee_id=committee_id
    ).count()

    log_method(f"Deleting Reports and Transactions for {committee_id}")
    log_method(f"Deleting Reports: {report_count}")
    log_method(f"Deleting Transactions: {transaction_count}")
    log_method(f"Memos: {memo_count}")
    log_method(f"Dot Fecs: {dot_fec_count}")
    log_method(f"Upload Submissions: {upload_submission_count}")
    log_method(f"WebPrint Submissions: {web_print_submission_count}")

    reports.delete()
    transactions.hard_delete()


def delete_committee_contacts(committee_id):
    Contact.objects.filter(committee_account__committee_id=committee_id).delete()
