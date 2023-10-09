from fecfiler.memo_text.models import MemoText
from fecfiler.reports.models import Report
from fecfiler.web_services.models import UploadSubmission
from fecfiler.transactions.models import Transaction
from fecfiler.transactions.managers import Schedule
from django.core.exceptions import ObjectDoesNotExist
from .dot_fec_serializer import serialize_instance, CRLF_STR
from fecfiler.settings import FILE_AS_TEST_COMMITTEE, OUTPUT_TEST_INFO_IN_DOT_FEC

import logging

logger = logging.getLogger(__name__)


def compose_f3x_report(report_id, upload_submission_record_id):
    report_result = Report.objects.filter(id=report_id)
    upload_submission_result = UploadSubmission.objects.filter(
        id=upload_submission_record_id
    )
    if report_result.exists():
        logger.info(f"composing f3x summary: {report_id}")
        f3x_report = report_result.first()
        """Compose derived fields"""
        f3x_report.filer_committee_id_number = (
            FILE_AS_TEST_COMMITTEE or f3x_report.committee_account.committee_id
        )
        if upload_submission_result.exists():
            f3x_report.date_signed = upload_submission_result.first().created
        return f3x_report
    else:
        raise ObjectDoesNotExist(f"report: {report_id} not found")


def compose_transactions(report_id):
    transactions = Transaction.objects.filter(report_id=report_id)
    if transactions.exists():
        logger.info(f"composing transactions: {report_id}")
        """Compose derived fields"""
        for transaction in transactions:
            transaction.filer_committee_id_number = (
                FILE_AS_TEST_COMMITTEE or transaction.committee_account.committee_id
            )
            # TODO: improve itemization inheritance.
            # We should not have to determine it here
            root_id = (
                transaction.parent_transaction.parent_transaction.id
                if transaction.parent_transaction
                and transaction.parent_transaction.parent_transaction
                else transaction.parent_transaction.id
                if transaction.parent_transaction
                else transaction.id
            )
            transaction.itemized = transactions.filter(id=root_id).first().itemized
        return [t for t in transactions if t.itemized]
    else:
        logger.info(f"no transactions found for report: {report_id}")
        return []


def compose_report_level_memos(report_id):
    report_level_memos = MemoText.objects.filter(
        report_id=report_id, transaction_uuid=None,
    )
    if report_level_memos.exists():
        logger.info(f"composing report level memos: {report_id}")
        for memo in report_level_memos:
            memo.filer_committee_id_number = (
                FILE_AS_TEST_COMMITTEE or memo.committee_account.committee_id
            )
        return report_level_memos
    else:
        logger.info(f"no report level memos found for report: {report_id}")
        return []


class Header:
    def __init__(
        self,
        record_type,
        ef_type,
        fec_version,
        soft_name,
        soft_ver,
        rpt_id=None,
        rpt_number=None,
        hdrcomment=None,
    ):
        self.record_type = record_type
        self.ef_type = ef_type
        self.fec_version = fec_version
        self.soft_name = soft_name
        self.soft_ver = soft_ver
        self.rpt_id = rpt_id
        self.rpt_number = rpt_number
        self.hdrcomment = hdrcomment


def compose_header():
    return Header("HDR", "FEC", "8.4", "FECFile Online", "0.0.1")


def add_row_to_content(content, row):
    """Returns new string with `row` appended to `content` and adds .FEC line breaks
    Args:
        content (string): .FEC content to add row to
        row (string): Row that will be appended to `content`
    """
    return (content or "") + str(row) + CRLF_STR


def get_schema_name(schedule):
    return {
        Schedule.A.value.value: "SchA",
        Schedule.B.value.value: "SchB",
        Schedule.C.value.value: "SchC",
        Schedule.C1.value.value: "SchC1",
        Schedule.C2.value.value: "SchC2",
        Schedule.D.value.value: "SchD",
    }.get(schedule)


def get_test_info_prefix(transaction):
    if OUTPUT_TEST_INFO_IN_DOT_FEC:
        return (
            f"(For Testing: {' l->' if transaction.parent_transaction else ''}"
            f" {transaction.schedule}, Line-Number: {transaction.form_type},"
            f" Created: {transaction.created})"
        )
    return ""


def compose_dot_fec(report_id, upload_submission_record_id):
    logger.info(f"composing .FEC for report: {report_id}")
    try:
        header = compose_header()
        header_row = serialize_instance("HDR", header)
        logger.debug("Serialized HDR:")
        logger.debug(header_row)
        file_content = add_row_to_content(None, header_row)

        f3x_report = compose_f3x_report(report_id, upload_submission_record_id)
        f3x_report_row = serialize_instance("F3X", f3x_report)
        logger.debug("Serialized F3X Report:")
        logger.debug(f3x_report_row)
        file_content = add_row_to_content(file_content, f3x_report_row)

        transactions = compose_transactions(report_id)
        for transaction in transactions:
            serialized_transaction = serialize_instance(
                get_schema_name(transaction.schedule), transaction
            )
            logger.debug("Serialized Transaction:")
            logger.debug(serialized_transaction)
            test_info_prefix = get_test_info_prefix(transaction)
            file_content = add_row_to_content(
                file_content, test_info_prefix + serialized_transaction
            )
            if transaction.memo_text:
                memo = transaction.memo_text
                memo.filer_committee_id_number = (
                    FILE_AS_TEST_COMMITTEE or memo.committee_account.committee_id
                )
                memo.back_reference_tran_id_number = transaction.transaction_id
                memo.back_reference_sched_form_name = transaction.form_type
                serialized_memo = serialize_instance("Text", memo)
                logger.debug("Serialized Memo:")
                logger.debug(serialized_memo)
                file_content = add_row_to_content(file_content, serialized_memo)

        report_level_memos = compose_report_level_memos(report_id)
        for memo in report_level_memos:
            memo.back_reference_sched_form_name = f3x_report.form_type
            serialized_memo = serialize_instance("Text", memo)
            logger.debug("Serialized Report Level Memo:")
            logger.debug(memo)
            file_content = add_row_to_content(file_content, serialized_memo)

        return file_content
    except Exception as error:
        logger.error(f"failed to compose .FEC for report {report_id}: {str(error)}")
        raise error
