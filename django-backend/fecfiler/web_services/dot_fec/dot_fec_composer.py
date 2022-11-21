from fecfiler.memo_text.models import MemoText
from fecfiler.f3x_summaries.models import F3XSummary
from fecfiler.web_services.models import UploadSubmission
from fecfiler.scha_transactions.models import SchATransaction
from django.core.exceptions import ObjectDoesNotExist
from .dot_fec_serializer import serialize_header, serialize_model_instance, CRLF_STR
from fecfiler.settings import FILE_AS_TEST_COMMITTEE

import logging

logger = logging.getLogger(__name__)


def compose_f3x_summary(report_id, upload_submission_record_id):
    f3x_summary_result = F3XSummary.objects.filter(id=report_id)
    upload_submission_result = UploadSubmission.objects.filter(
        id=upload_submission_record_id
    )
    if f3x_summary_result.exists():
        logger.info(f"composing f3x summary: {report_id}")
        f3x_summary = f3x_summary_result.first()
        """Compose derived fields"""
        f3x_summary.filer_committee_id_number = (
            FILE_AS_TEST_COMMITTEE or f3x_summary.committee_account.committee_id
        )
        if upload_submission_result.exists():
            f3x_summary.date_signed = upload_submission_result.first().created
        return f3x_summary
    else:
        raise ObjectDoesNotExist(f"report: {report_id} not found")


def compose_transactions(report_id):
    transactions = SchATransaction.objects.filter(report_id=report_id, itemized=True)
    if transactions.exists():
        logger.info(f"composing transactions: {report_id}")
        """Compose derived fields"""
        for transaction in transactions:
            transaction.filer_committee_id_number = (
                FILE_AS_TEST_COMMITTEE or transaction.committee_account.committee_id
            )
        return transactions
    else:
        logger.info(f"no transactions found for report: {report_id}")
        return []


def compose_report_level_memos(report_id):
    report_level_memos = MemoText.objects.filter(
        report_id=report_id,
        transaction_uuid=None,
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


def compose_header():
    return {
        "record_type": "HDR",
        "ef_type": "FEC",
        "fec_version": "8.4",
        "soft_name": "FECFile Online",
        "soft_ver": "0.0.1",
        "rpt_id": None,
        "rpt_number": None,
        "hdrcomment": None,
    }


def add_row_to_content(content, row):
    """Returns new string with `row` appended to `content` and adds .FEC line breaks
    Args:
        content (string): .FEC content to add row to
        row (string): Row that will be appended to `content`
    """
    return (content or "") + str(row) + CRLF_STR


def compose_dot_fec(report_id, upload_submission_record_id):
    logger.info(f"composing .FEC for report: {report_id}")
    try:
        header = compose_header()
        header_row = serialize_header(header)
        logger.debug("Serialized HDR:")
        logger.debug(header_row)
        file_content = add_row_to_content(None, header_row)

        f3x_summary = compose_f3x_summary(report_id, upload_submission_record_id)
        f3x_summary_row = serialize_model_instance("F3X", F3XSummary, f3x_summary)
        logger.debug("Serialized Report Summary:")
        logger.debug(f3x_summary_row)
        file_content = add_row_to_content(file_content, f3x_summary_row)

        transactions = compose_transactions(report_id)
        for transaction in transactions:
            serialized_transaction = serialize_model_instance(
                "SchA", SchATransaction, transaction
            )
            logger.debug("Serialized Transaction:")
            logger.debug(serialized_transaction)
            file_content = add_row_to_content(file_content, serialized_transaction)
            if transaction.memo_text:
                memo = transaction.memo_text
                memo.back_reference_tran_id_number = transaction.transaction_id
                memo.back_reference_sched_name = transaction.form_type
                serialized_memo = serialize_model_instance("Text", MemoText, memo)
                logger.debug("Serialized Memo:")
                logger.debug(serialized_memo)
                file_content = add_row_to_content(file_content, serialized_memo)

        report_level_memos = compose_report_level_memos(report_id)
        report_level_memo_rows = [
            serialize_model_instance("Text", MemoText, memo)
            for memo in report_level_memos
        ]
        for memo in report_level_memo_rows:
            logger.debug("Serialized Report Level Memo:")
            logger.debug(memo)
            file_content = add_row_to_content(file_content, memo)

        return file_content
    except Exception as error:
        logger.error(f"failed to compose .FEC for report {report_id}: {str(error)}")
        raise error
