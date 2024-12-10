from decimal import Decimal
from fecfiler.memo_text.models import MemoText
from fecfiler.reports.models import Report
from fecfiler.transactions.models import get_read_model
from fecfiler.transactions.managers import Schedule
from django.core.exceptions import ObjectDoesNotExist
from .dot_fec_serializer import serialize_instance, CRLF_STR
from fecfiler.settings import OUTPUT_TEST_INFO_IN_DOT_FEC
from fecfiler.transactions.schedule_a.utils import add_schedule_a_contact_fields
from fecfiler.transactions.schedule_b.utils import add_schedule_b_contact_fields
from fecfiler.transactions.schedule_c.utils import add_schedule_c_contact_fields
from fecfiler.transactions.schedule_c1.utils import add_schedule_c1_contact_fields
from fecfiler.transactions.schedule_c2.utils import add_schedule_c2_contact_fields
from fecfiler.transactions.schedule_d.utils import add_schedule_d_contact_fields
from fecfiler.transactions.schedule_e.utils import add_schedule_e_contact_fields
import structlog

logger = structlog.get_logger(__name__)


def compose_report(report_id):
    report_result = Report.objects.filter(id=report_id)
    if report_result.exists():
        logger.info(f"composing report: {report_id}")
        report = report_result.first()
        """Compose derived fields"""
        report.filer_committee_id_number = report.committee_account.committee_id

        return report
    else:
        raise ObjectDoesNotExist(f"report: {report_id} not found")


def compose_transactions(report_id):
    report = Report.objects.get(id=report_id)
    transaction_view_model = get_read_model(report.committee_account_id)
    transactions = transaction_view_model.objects.filter(reports__id=report_id)
    if transactions.exists():
        logger.info(f"composing transactions: {report_id}")
        """Compose derived fields"""
        for transaction in transactions:
            if transaction.schedule_a:
                add_schedule_a_contact_fields(transaction)
            if transaction.schedule_b:
                add_schedule_b_contact_fields(transaction)
            if transaction.schedule_c:
                loan_amount = (
                    transaction.schedule_c.loan_amount
                    if transaction.schedule_c.loan_amount is not None
                    else Decimal("0.00")
                )

                transaction.loan_payment_to_date = (
                    transaction.loan_payment_to_date
                    if transaction.loan_payment_to_date is not None
                    else Decimal("0.00")
                )
                transaction.loan_balance = loan_amount - transaction.loan_payment_to_date
                add_schedule_c_contact_fields(transaction)
            if transaction.schedule_c1:
                add_schedule_c1_contact_fields(transaction)
            if transaction.schedule_c2:
                add_schedule_c2_contact_fields(transaction)
            if transaction.schedule_d:
                add_schedule_d_contact_fields(transaction)
            if transaction.schedule_e:
                add_schedule_e_contact_fields(transaction)

        return [t for t in transactions if (t.itemized or report.form_24 is not None)]
    else:
        logger.info(f"no transactions found for report: {report_id}")
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


def compose_header(report_id):
    report_result = Report.objects.filter(id=report_id)
    if report_result.exists():
        report = report_result.first()
        logger.info(f"composing header: {report_id}")
        return Header(
            "HDR",
            "FEC",
            "8.4",
            "FECFile Online",
            "0.0.1",
            report.report_id,
            report.report_version,
        )
    else:
        raise ObjectDoesNotExist(f"header: {report_id} not found")


def add_row_to_content(content, row):
    """Returns new string with `row` appended to `content` and adds .FEC line breaks
    Args:
        content (string): .FEC content to add row to
        row (string): Row that will be appended to `content`
    """
    return (content or "") + str(row) + CRLF_STR


def add_free_text(content, text):
    """Returns new string with free text wrapped with begin/end markers"""
    return (
        (content or "")
        + "[BEGINTEXT]"
        + CRLF_STR
        + (text or "")
        + CRLF_STR
        + "[ENDTEXT]"
        + CRLF_STR
    )


def get_schema_name(schedule):
    return {
        Schedule.A.value.value: "SchA",
        Schedule.B.value.value: "SchB",
        Schedule.C.value.value: "SchC",
        Schedule.C1.value.value: "SchC1",
        Schedule.C2.value.value: "SchC2",
        Schedule.D.value.value: "SchD",
        Schedule.E.value.value: "SchE",
    }.get(schedule)


def get_test_info_prefix(transaction):
    if OUTPUT_TEST_INFO_IN_DOT_FEC:
        return (
            f"(For Testing: {' l->' if transaction.parent_transaction else ''}"
            f" {transaction.schedule}, Line-Number: {transaction.form_type},"
            f" Created: {transaction.created})"
        )
    return ""


def compose_dot_fec(report_id):
    logger.info(f"composing .FEC for report: {report_id}")
    try:
        header = compose_header(report_id)
        header_row = serialize_instance("HDR", header)
        logger.debug("Serialized HDR:")
        logger.debug(header_row)
        file_content = add_row_to_content(None, header_row)

        report = compose_report(report_id)
        report_row = serialize_instance(report.get_form_name(), report)
        logger.debug("Serialized Report:")
        logger.debug(report_row)
        file_content = add_row_to_content(file_content, report_row)

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
                serialized_memo = serialize_instance("Text", memo)
                logger.debug("Serialized Memo:")
                logger.debug(serialized_memo)
                file_content = add_row_to_content(file_content, serialized_memo)

        report_level_memos = MemoText.objects.filter(
            report_id=report_id,
            transaction_uuid=None,
        )
        for memo in report_level_memos:
            serialized_memo = serialize_instance("Text", memo)
            logger.debug("Serialized Report Level Memo:")
            logger.debug(memo)
            file_content = add_row_to_content(file_content, serialized_memo)

        """Free text"""
        if report.get_form_name() == "F99":
            file_content = add_free_text(file_content, report.form_99.message_text)

        return file_content
    except Exception as error:
        logger.error(f"failed to compose .FEC for report {report_id}: {str(error)}")
        raise error
