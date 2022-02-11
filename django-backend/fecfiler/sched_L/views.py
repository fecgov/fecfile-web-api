import datetime
import logging

from django.db import connection
from django.http import JsonResponse
from django.core.paginator import Paginator
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from fecfiler.authentication.authorization import is_read_only_or_filer_reports
from fecfiler.core.views import (
    NoOPError,
    check_null_value,
    check_report_id,
    get_cvg_dates,
    get_levin_account,
    get_comittee_id,
    get_report_ids,
)

from fecfiler.core.transaction_util import (
    get_sched_a_transactions,
    get_transaction_type_descriptions,
    do_transaction,
)

# from fecfiler.sched_A.views import get_next_transaction_id
# from fecfiler.sched_D.views import do_transaction


# Create your views here.
logger = logging.getLogger(__name__)

MANDATORY_FIELDS_SCHED_L = ["cmte_id", "report_id", "transaction_id", "record_id"]

LA_TRANSACTIONS = [
    "LEVIN_OTH_REC",
    "LEVIN_PARTN_MEMO",
    "LEVIN_PARTN_REC",
    "LEVIN_TRIB_REC",
    "LEVIN_ORG_REC",
    "LEVIN_INDV_REC",
    "LEVIN_NON_FED_REC",
    "LEVIN_PAC_REC",
]

LB_TRANSACTIONS = [
    "LEVIN_VOTER_ID",
    "LEVIN_GOTV",
    "LEVIN_GEN",
    "LEVIN_OTH_DISB",
    "LEVIN_VOTER_REG",
]

API_CALL_LA = {"api_call": "/sa/schedA"}
API_CALL_LB = {"api_call": "/sb/schedB"}


def get_next_transaction_id(trans_char):
    """get next transaction_id with seeding letter, like 'SA'"""
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """SELECT public.get_next_transaction_id(%s)""", [trans_char]
            )
            transaction_id = cursor.fetchone()[0]
            # transaction_id = transaction_ids[0]
        return transaction_id
    except Exception:
        raise


def check_transaction_id(transaction_id):
    if not (transaction_id[0:2] == "SL"):
        raise Exception(
            "The Transaction ID: {} is not in the specified format."
            "Transaction IDs start with SL characters".format(transaction_id)
        )
    return transaction_id


def check_mandatory_fields_SL(data):
    """
    validate mandatory fields for sched_L item
    """
    try:
        errors = []
        for field in MANDATORY_FIELDS_SCHED_L:
            if not (field in data and check_null_value(data.get(field))):
                errors.append(field)
        if errors:
            raise Exception(
                "The following mandatory fields are required in order to save data to schedL table: {}".format(
                    ",".join(errors)
                )
            )
    except BaseException:
        raise


def schedL_sql_dict(data):
    """
    filter out valid fileds for sched_L

    """
    valid_fields = [
        "cmte_id",
        "report_id",
        "transaction_type_identifier",
        "line_number",
        "record_id",
        "account_name",
        "cvg_from_date",
        "cvg_end_date",
        "item_receipts",
        "unitem_receipts",
        "total_c_receipts",
        "other_receipts",
        "total_receipts",
        "voter_reg_disb_amount",
        "voter_id_disb_amount",
        "gotv_disb_amount",
        "generic_campaign_disb_amount",
        "total_disb_sub",
        "other_disb",
        "total_disb",
        "coh_bop",
        "receipts",
        "subtotal",
        "disbursements",
        "coh_cop",
        "item_receipts_ytd",
        "unitem_receipts_ytd",
        "total_c_receipts_ytd",
        "other_receipts_ytd",
        "total_receipts_ytd",
        "voter_reg_disb_amount_ytd",
        "voter_id_disb_amount_ytd",
        "gotv_disb_amount_ytd",
        "generic_campaign_disb_amount_ytd",
        "total_disb_sub_ytd",
        "other_disb_ytd",
        "total_disb_ytd",
        "coh_coy",
        "receipts_ytd",
        "sub_total_ytd",
        "disbursements_ytd",
        "coh_cop_ytd",
    ]
    try:
        valid_data = {k: v for k, v in data.items() if k in valid_fields}

        return valid_data
    except BaseException:
        raise Exception("invalid request data.")


def put_schedL(data):
    """
    update sched_L item
    here we are assuming entity_id are always referencing something already in our DB
    """
    try:
        check_mandatory_fields_SL(data)
        # check_transaction_id(data.get('transaction_id'))
        try:
            logger.debug("update sl record with {}".format(data))
            put_sql_schedL(data)
        except Exception as e:
            raise Exception(
                "The put_sql_schedL function is throwing an error: " + str(e)
            )
        return data
    except BaseException:
        raise


def put_sql_schedL(data):
    """
    update a schedule_L item
    """
    _sql = """UPDATE public.sched_l
              SET transaction_type_identifier = %s,
                  line_number = %s,
                  record_id = %s,
                  account_name = %s,
                  cvg_from_date = %s,
                  cvg_end_date = %s,
                  item_receipts = %s,
                  unitem_receipts = %s,
                  total_c_receipts = %s,
                  other_receipts = %s,
                  total_receipts = %s,
                  voter_reg_disb_amount = %s,
                  voter_id_disb_amount = %s,
                  gotv_disb_amount = %s,
                  generic_campaign_disb_amount = %s,
                  total_disb_sub = %s,
                  other_disb = %s,
                  total_disb = %s,
                  coh_bop = %s,
                  receipts = %s,
                  subtotal = %s,
                  disbursements = %s,
                  coh_cop = %s,
                  item_receipts_ytd = %s,
                  unitem_receipts_ytd = %s,
                  total_c_receipts_ytd = %s,
                  other_receipts_ytd = %s,
                  total_receipts_ytd = %s,
                  voter_reg_disb_amount_ytd = %s,
                  voter_id_disb_amount_ytd = %s,
                  gotv_disb_amount_ytd = %s,
                  generic_campaign_disb_amount_ytd = %s,
                  total_disb_sub_ytd = %s,
                  other_disb_ytd = %s,
                  total_disb_ytd = %s,
                  coh_coy = %s,
                  receipts_ytd = %s,
                  sub_total_ytd = %s,
                  disbursements_ytd = %s,
                  coh_cop_ytd = %s,
                  create_date = %s,
                  last_update_date= %s
              WHERE transaction_id = %s AND report_id = %s AND cmte_id = %s
              AND delete_ind is distinct from 'Y';
        """
    _v = (
        data.get("transaction_type_identifier"),
        data.get("line_number"),
        data.get("record_id"),
        data.get("account_name"),
        data.get("cvg_from_date"),
        data.get("cvg_end_date"),
        data.get("item_receipts"),
        data.get("unitem_receipts"),
        data.get("total_c_receipts"),
        data.get("other_receipts"),
        data.get("total_receipts"),
        data.get("voter_reg_disb_amount"),
        data.get("voter_id_disb_amount"),
        data.get("gotv_disb_amount"),
        data.get("generic_campaign_disb_amount"),
        data.get("total_disb_sub"),
        data.get("other_disb"),
        data.get("total_disb"),
        data.get("coh_bop"),
        data.get("receipts"),
        data.get("subtotal"),
        data.get("disbursements"),
        data.get("coh_cop"),
        data.get("item_receipts_ytd"),
        data.get("unitem_receipts_ytd"),
        data.get("total_c_receipts_ytd"),
        data.get("other_receipts_ytd"),
        data.get("total_receipts_ytd"),
        data.get("voter_reg_disb_amount_ytd"),
        data.get("voter_id_disb_amount_ytd"),
        data.get("gotv_disb_amount_ytd"),
        data.get("generic_campaign_disb_amount_ytd"),
        data.get("total_disb_sub_ytd"),
        data.get("other_disb_ytd"),
        data.get("total_disb_ytd"),
        data.get("coh_coy"),
        data.get("receipts_ytd"),
        data.get("sub_total_ytd"),
        data.get("disbursements_ytd"),
        data.get("coh_cop_ytd"),
        datetime.datetime.now(),
        datetime.datetime.now(),
        data.get("transaction_id"),
        data.get("report_id"),
        data.get("cmte_id"),
    )
    do_transaction(_sql, _v)


def validate_sl_data(data):
    """
    validate sL json data
    """
    check_mandatory_fields_SL(data)


def post_schedL(data):
    """
    function for handling POST request for sL, need to:
    1. generatye new transaction_id
    2. validate data
    3. save data to db
    """
    try:
        # check_mandatory_fields_SL(datum, MANDATORY_FIELDS_SCHED_L)
        data["transaction_id"] = get_next_transaction_id("SL")
        validate_sl_data(data)
        try:
            post_sql_schedL(data)
        except Exception as e:
            raise Exception(
                "The post_sql_schedL function is throwing an error: " + str(e)
            )
        return data
    except BaseException:
        raise


def post_sql_schedL(data):
    try:
        _sql = """
        INSERT INTO public.sched_l (
            cmte_id,
            report_id,
            transaction_type_identifier,
            line_number,
            transaction_id,
            record_id,
            account_name,
            cvg_from_date,
            cvg_end_date,
            item_receipts,
            unitem_receipts,
            other_receipts,
            total_receipts,
            voter_reg_disb_amount,
            voter_id_disb_amount,
            gotv_disb_amount,
            generic_campaign_disb_amount,
            total_disb_sub,
            other_disb,
            total_disb,
            coh_bop,
            receipts,
            subtotal,
            disbursements,
            coh_cop,
            item_receipts_ytd,
            unitem_receipts_ytd,
            other_receipts_ytd,
            total_receipts_ytd,
            voter_reg_disb_amount_ytd,
            voter_id_disb_amount_ytd,
            gotv_disb_amount_ytd,
            generic_campaign_disb_amount_ytd,
            total_disb_sub_ytd,
            other_disb_ytd,
            total_disb_ytd,
            coh_coy,
            receipts_ytd,
            sub_total_ytd,
            disbursements_ytd,
            coh_cop_ytd,
            create_date,
            last_update_date
            )
        VALUES ({})
        """.format(
            ",".join(["%s"] * 43)
        )
        _v = (
            data.get("cmte_id"),
            data.get("report_id"),
            data.get("transaction_type_identifier"),
            data.get("line_number"),
            data.get("transaction_id"),
            data.get("record_id"),
            data.get("account_name"),
            data.get("cvg_from_date"),
            data.get("cvg_end_date"),
            data.get("item_receipts"),
            data.get("unitem_receipts"),
            data.get("other_receipts"),
            data.get("total_receipts"),
            data.get("voter_reg_disb_amount"),
            data.get("voter_id_disb_amount"),
            data.get("gotv_disb_amount"),
            data.get("generic_campaign_disb_amount"),
            data.get("total_disb_sub"),
            data.get("other_disb"),
            data.get("total_disb"),
            data.get("coh_bop"),
            data.get("receipts"),
            data.get("subtotal"),
            data.get("disbursements"),
            data.get("coh_cop"),
            data.get("item_receipts_ytd"),
            data.get("unitem_receipts_ytd"),
            data.get("other_receipts_ytd"),
            data.get("total_receipts_ytd"),
            data.get("voter_reg_disb_amount_ytd"),
            data.get("voter_id_disb_amount_ytd"),
            data.get("gotv_disb_amount_ytd"),
            data.get("generic_campaign_disb_amount_ytd"),
            data.get("total_disb_sub_ytd"),
            data.get("other_disb_ytd"),
            data.get("total_disb_ytd"),
            data.get("coh_coy"),
            data.get("receipts_ytd"),
            data.get("sub_total_ytd"),
            data.get("disbursements_ytd"),
            data.get("coh_cop_ytd"),
            datetime.datetime.now(),
            datetime.datetime.now(),
        )
        with connection.cursor() as cursor:
            # Insert data into schedL table
            cursor.execute(_sql, _v)
    except Exception:
        raise


def get_schedL(data):
    """
    load sched_L data based on cmte_id, report_id and transaction_id
    """
    try:
        cmte_id = data.get("cmte_id")
        report_id = data.get("report_id")
        if "transaction_id" in data:
            transaction_id = check_transaction_id(data.get("transaction_id"))
            forms_obj = get_list_schedL(report_id, cmte_id, transaction_id)
        else:
            forms_obj = get_list_all_schedL(report_id, cmte_id)
        return forms_obj
    except BaseException:
        raise


def get_list_all_schedL(report_id, cmte_id):

    try:
        with connection.cursor() as cursor:
            # GET single row from schedL table
            _sql = """SELECT json_agg(t) FROM ( SELECT
            cmte_id,
            report_id,
            transaction_type_identifier,
            line_number,
            transaction_id,
            record_id,
            account_name,
            cvg_from_date,
            cvg_end_date,
            item_receipts,
            unitem_receipts,
            other_receipts,
            total_receipts,
            voter_reg_disb_amount,
            voter_id_disb_amount,
            gotv_disb_amount,
            generic_campaign_disb_amount,
            total_disb_sub,
            other_disb,
            total_disb,
            coh_bop,
            receipts,
            subtotal,
            disbursements,
            coh_cop,
            item_receipts_ytd,
            unitem_receipts_ytd,
            other_receipts_ytd,
            total_receipts_ytd,
            voter_reg_disb_amount_ytd,
            voter_id_disb_amount_ytd,
            gotv_disb_amount_ytd,
            generic_campaign_disb_amount_ytd,
            total_disb_sub_ytd,
            other_disb_ytd,
            total_disb_ytd,
            coh_coy,
            receipts_ytd,
            sub_total_ytd,
            disbursements_ytd,
            coh_cop_ytd,
            delete_ind,
            create_date ,
            last_update_date
            FROM public.sched_l
            WHERE report_id = %s AND cmte_id = %s
            AND delete_ind is distinct from 'Y') t
            """
            cursor.execute(_sql, (report_id, cmte_id))
            schedl_list = cursor.fetchone()[0]
            if schedl_list is None:
                raise NoOPError(
                    "No sched_L transaction found for report_id {} and cmte_id: {}".format(
                        report_id, cmte_id
                    )
                )
            merged_list = []
            for dictL in schedl_list:
                merged_list.append(dictL)
        return merged_list
    except Exception:
        raise


def get_list_schedL(report_id, cmte_id, transaction_id):
    try:
        with connection.cursor() as cursor:
            # GET single row from schedL table
            _sql = """SELECT json_agg(t) FROM ( SELECT
            cmte_id,
            report_id,
            transaction_type_identifier,
            line_number,
            transaction_id,
            record_id,
            account_name,
            cvg_from_date,
            cvg_end_date,
            item_receipts,
            unitem_receipts,
            other_receipts,
            total_receipts,
            voter_reg_disb_amount,
            voter_id_disb_amount,
            gotv_disb_amount,
            generic_campaign_disb_amount,
            total_disb_sub,
            other_disb,
            total_disb,
            coh_bop,
            receipts,
            subtotal,
            disbursements,
            coh_cop,
            item_receipts_ytd,
            unitem_receipts_ytd,
            other_receipts_ytd,
            total_receipts_ytd,
            voter_reg_disb_amount_ytd,
            voter_id_disb_amount_ytd,
            gotv_disb_amount_ytd,
            generic_campaign_disb_amount_ytd,
            total_disb_sub_ytd,
            other_disb_ytd,
            total_disb_ytd,
            coh_coy,
            receipts_ytd,
            sub_total_ytd,
            disbursements_ytd,
            coh_cop_ytd,
            delete_ind,
            create_date ,
            last_update_date
            FROM public.sched_l
            WHERE report_id = %s AND cmte_id = %s AND transaction_id = %s
            AND delete_ind is distinct from 'Y') t
            """
            cursor.execute(_sql, (report_id, cmte_id, transaction_id))
            schedL_list = cursor.fetchone()[0]
            if schedL_list is None:
                raise NoOPError(
                    "No sched_L transaction found for transaction_id {}".format(
                        transaction_id
                    )
                )
            merged_list = []
            for dictL in schedL_list:
                merged_list.append(dictL)
        return merged_list
    except Exception:
        raise


def delete_sql_schedL(cmte_id, report_id, transaction_id):
    """
    do delete sql transaction
    """
    _sql = """UPDATE public.sched_l
            SET delete_ind = 'Y'
            WHERE transaction_id = %s AND report_id = %s AND cmte_id = %s
        """
    _v = (transaction_id, report_id, cmte_id)
    do_transaction(_sql, _v)


def delete_schedL(data):
    """
    function for handling delete request for sl
    """
    try:

        delete_sql_schedL(
            data.get("cmte_id"), data.get("report_id"), data.get("transaction_id")
        )
    except Exception as e:
        raise e


@api_view(["POST", "GET", "DELETE", "PUT"])
def schedL(request):

    try:
        is_read_only_or_filer_reports(request)

        if request.method == "POST":
            try:
                cmte_id = get_comittee_id(request.user.username)

                if not ("report_id" in request.data):
                    raise Exception("Missing Input: Report_id is mandatory")
                # handling null,none value of report_id
                if not (check_null_value(request.data.get("report_id"))):
                    report_id = "0"
                else:
                    report_id = check_report_id(request.data.get("report_id"))
                # end of handling
                logger.debug("sched_l POST with data:{}".format(request.data))
                datum = schedL_sql_dict(request.data)
                logger.debug(datum)
                datum["report_id"] = report_id
                datum["cmte_id"] = cmte_id
                # populate levin account info: record_id is levin_account_id
                if "levin_account_id" in request.data:
                    levin_acct_id = request.data.get("levin_account_id")
                    datum["record_id"] = levin_acct_id
                    levin_account = get_levin_account(cmte_id, levin_acct_id)
                    if levin_account:
                        datum["account_name"] = levin_account[0].get(
                            "levin_account_name"
                        )
                if "transaction_id" in request.data and check_null_value(
                    request.data.get("transaction_id")
                ):
                    datum["transaction_id"] = check_transaction_id(
                        request.data.get("transaction_id")
                    )
                    data = put_schedL(datum)
                else:
                    data = post_schedL(datum)
                # Associating child transactions to parent and storing them to DB

                output = get_schedL(data)
                return JsonResponse(output[0], status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response(
                    "The schedL API - POST is throwing an exception: " + str(e),
                    status=status.HTTP_400_BAD_REQUEST,
                )

        elif request.method == "GET":
            try:
                data = {"cmte_id": get_comittee_id(request.user.username)}
                if "report_id" in request.query_params and check_null_value(
                    request.query_params.get("report_id")
                ):
                    data["report_id"] = check_report_id(
                        request.query_params.get("report_id")
                    )
                else:
                    raise Exception("Missing Input: report_id is mandatory")
                if "transaction_id" in request.query_params and check_null_value(
                    request.query_params.get("transaction_id")
                ):
                    data["transaction_id"] = check_transaction_id(
                        request.query_params.get("transaction_id")
                    )
                datum = get_schedL(data)
                return JsonResponse(datum, status=status.HTTP_200_OK, safe=False)
            except NoOPError as e:
                logger.debug(e)
                forms_obj = []
                return JsonResponse(
                    forms_obj, status=status.HTTP_204_NO_CONTENT, safe=False
                )
            except Exception as e:
                logger.debug(e)
                return Response(
                    "The schedL API - GET is throwing an error: " + str(e),
                    status=status.HTTP_400_BAD_REQUEST,
                )

        elif request.method == "DELETE":
            try:
                data = {"cmte_id": get_comittee_id(request.user.username)}
                if "report_id" in request.data and check_null_value(
                    request.data.get("report_id")
                ):
                    data["report_id"] = check_report_id(request.data.get("report_id"))
                else:
                    raise Exception("Missing Input: report_id is mandatory")
                if "transaction_id" in request.data and check_null_value(
                    request.data.get("transaction_id")
                ):
                    data["transaction_id"] = check_transaction_id(
                        request.data.get("transaction_id")
                    )
                else:
                    raise Exception("Missing Input: transaction_id is mandatory")
                delete_schedL(data)
                return Response(
                    "The Transaction ID: {} has been successfully deleted".format(
                        data.get("transaction_id")
                    ),
                    status=status.HTTP_201_CREATED,
                )
            except Exception as e:
                return Response(
                    "The schedL API - DELETE is throwing an error: " + str(e),
                    status=status.HTTP_400_BAD_REQUEST,
                )

        elif request.method == "PUT":
            try:
                datum = schedL_sql_dict(request.data)
                if "transaction_id" in request.data and check_null_value(
                    request.data.get("transaction_id")
                ):
                    datum["transaction_id"] = request.data.get("transaction_id")
                else:
                    raise Exception("Missing Input: transaction_id is mandatory")

                if not ("report_id" in request.data):
                    raise Exception("Missing Input: Report_id is mandatory")
                # handling null,none value of report_id
                if not (check_null_value(request.data.get("report_id"))):
                    report_id = "0"
                else:
                    report_id = check_report_id(request.data.get("report_id"))
                # end of handling
                datum["report_id"] = report_id
                datum["cmte_id"] = get_comittee_id(request.user.username)
                if "levin_account_id" in request.data:
                    levin_acct_id = request.data.get("levin_account_id")
                    datum["record_id"] = levin_acct_id
                    levin_account = get_levin_account(cmte_id, levin_acct_id)
                    if levin_account:
                        datum["account_name"] = levin_account[0].get(
                            "levin_account_name"
                        )
                # if 'entity_id' in request.data and check_null_value(request.data.get('entity_id')):
                #     datum['entity_id'] = request.data.get('entity_id')
                # if request.data.get('transaction_type') in CHILD_SCHED_B_TYPES:
                #     data = put_schedB(datum)
                #     output = get_schedB(data)
                # else:
                data = put_schedL(datum)
                # output = get_schedA(data)
                return JsonResponse(data, status=status.HTTP_201_CREATED)
            except Exception as e:
                logger.debug(e)
                return Response(
                    "The schedL API - PUT is throwing an error: " + str(e),
                    status=status.HTTP_400_BAD_REQUEST,
                )

    except Exception as e:
        json_result = {"message": str(e)}
        return JsonResponse(json_result, status=status.HTTP_403_FORBIDDEN, safe=False)


def load_ytd_disbursements_summary(cmte_id, start_dt, end_dt, levin_account_id=None):
    """
    load year_to_date disbursement amount
    """
    result = {}
    result["voter_reg_disb_amount_ytd"] = 0
    result["voter_id_disb_amount_ytd"] = 0
    result["gotv_disb_amount_ytd"] = 0
    result["generic_campaign_disb_amount_ytd"] = 0
    result["other_disb_ytd"] = 0
    if levin_account_id:
        _sql = """
            SELECT t1.transaction_type_identifier, COALESCE(sum(t1.expenditure_amount),0) as total_amt
            FROM public.sched_b t1
            WHERE t1.memo_code IS NULL
            AND t1.cmte_id = %s
            AND t1.expenditure_date BETWEEN %s and %s
            AND t1.levin_account_id = %s
            AND t1.delete_ind is distinct from 'Y'
            AND substr(t1.transaction_type_identifier,1,6) = 'LEVIN_'
            GROUP BY t1.transaction_type_identifier
        """
    else:
        _sql = """
            SELECT t1.transaction_type_identifier, COALESCE(sum(t1.expenditure_amount),0) as total_amt
            FROM public.sched_b t1
            WHERE t1.memo_code IS NULL
            AND t1.cmte_id = %s
            AND t1.expenditure_date BETWEEN %s and %s
            AND t1.delete_ind is distinct from 'Y'
            AND substr(t1.transaction_type_identifier,1,6) = 'LEVIN_'
            GROUP BY t1.transaction_type_identifier
        """
    try:
        logger.debug("loading LB ytd...")
        with connection.cursor() as cursor:
            if levin_account_id:
                cursor.execute(_sql, (cmte_id, start_dt, end_dt, levin_account_id))
            else:
                cursor.execute(_sql, (cmte_id, start_dt, end_dt))
            if cursor.rowcount:
                for row in cursor.fetchall():
                    if row[0] == "LEVIN_VOTER_REG":
                        result["voter_reg_disb_amount_ytd"] = row[1]
                    elif row[0] == "LEVIN_VOTER_ID":
                        result["voter_id_disb_amount_ytd"] = row[1]
                    elif row[0] == "LEVIN_GOTV":
                        result["gotv_disb_amount_ytd"] = row[1]
                    elif row[0] == "LEVIN_GEN":
                        result["generic_campaign_disb_amount_ytd"] = row[1]
                    elif row[0] == "LEVIN_OTH_DISB":
                        result["other_disb_ytd"] = row[1]
                    else:
                        pass
            result["total_disb_sub_ytd"] = (
                float(result["voter_reg_disb_amount_ytd"])
                + float(result["voter_id_disb_amount_ytd"])
                + float(result["gotv_disb_amount_ytd"])
                + float(result["generic_campaign_disb_amount_ytd"])
            )
            result["total_disb_ytd"] = float(result["other_disb_ytd"]) + float(
                result["total_disb_sub_ytd"]
            )
    except Exception as e:
        raise Exception(
            "Error happens when query and calcualte dsibursements:" + str(e)
        )
    logger.debug("LB ytd data:{}".format(result))
    return result


def load_ytd_receipts_summary(cmte_id, start_dt, end_dt, levin_account_id=None):
    """
    load year_to_date receipt aggregation amount
    """
    result = {}
    result["item_receipts_ytd"] = 0
    result["unitem_receipts_ytd"] = 0
    result["other_receipts_ytd"] = 0

    if levin_account_id:
        _sql1 = """
            SELECT (CASE WHEN t1.aggregate_amt > 200 THEN 'Y' ELSE 'N' END) as item_ind, COALESCE(sum(contribution_amount),0) as total_amt
            FROM public.sched_a t1
            WHERE t1.memo_code IS NULL
            AND t1.cmte_id = %s
            AND t1.contribution_date BETWEEN %s AND %s
            AND t1.levin_account_id = %s
            AND t1.delete_ind is distinct from 'Y'
            AND substr(t1.transaction_type_identifier,1,5) = 'LEVIN'
            AND t1.transaction_type_identifier != 'LEVIN_OTH_REC'
            GROUP BY item_ind
        """

        _sql2 = """
            SELECT COALESCE(sum(contribution_amount),0)
            FROM public.sched_a t1
            WHERE t1.memo_code IS NULL
            AND t1.cmte_id = %s
            AND t1.contribution_date BETWEEN %s AND %s
            AND t1.levin_account_id = %s
            AND t1.delete_ind is distinct from 'Y'
            AND transaction_type_identifier = 'LEVIN_OTH_REC'
        """

    else:
        _sql1 = """
            SELECT (CASE WHEN t1.aggregate_amt > 200 THEN 'Y' ELSE 'N' END) as item_ind, COALESCE(sum(contribution_amount),0) as total_amt
            FROM public.sched_a t1
            WHERE t1.memo_code IS NULL
            AND t1.cmte_id = %s
            AND t1.contribution_date BETWEEN %s AND %s
            AND t1.delete_ind is distinct from 'Y'
            AND substr(t1.transaction_type_identifier,1,5) = 'LEVIN'
            AND t1.transaction_type_identifier != 'LEVIN_OTH_REC'
            GROUP BY item_ind
        """

        _sql2 = """
            SELECT COALESCE(sum(contribution_amount),0)
            FROM public.sched_a t1
            WHERE t1.memo_code IS NULL
            AND t1.cmte_id = %s
            AND t1.contribution_date BETWEEN %s AND %s
            AND t1.delete_ind is distinct from 'Y'
            AND transaction_type_identifier = 'LEVIN_OTH_REC'
        """

    try:
        logger.debug("loading LA ytd...")
        with connection.cursor() as cursor:
            if levin_account_id:
                cursor.execute(_sql1, (cmte_id, start_dt, end_dt, levin_account_id))
            else:
                cursor.execute(_sql1, (cmte_id, start_dt, end_dt))
            if cursor.rowcount:
                rows = cursor.fetchall()
                for row in rows:
                    if row[0] == "Y":
                        result["item_receipts_ytd"] = row[1]
                    elif row[0] == "N":
                        result["unitem_receipts_ytd"] = row[1]
                    else:
                        pass
            result["total_c_receipts_ytd"] = float(result["item_receipts_ytd"]) + float(
                result["unitem_receipts_ytd"]
            )

            if levin_account_id:
                cursor.execute(_sql2, (cmte_id, start_dt, end_dt, levin_account_id))
            else:
                cursor.execute(_sql2, (cmte_id, start_dt, end_dt))
            if cursor.rowcount:
                result["other_receipts_ytd"] = cursor.fetchone()[0]

            result["total_receipts_ytd"] = float(
                result["total_c_receipts_ytd"]
            ) + float(result["other_receipts_ytd"])

    except Exception as e:
        raise Exception("Error happens when query ytd receipts amount:" + str(e))
    logger.debug("LA ytd data:{}".format(result))
    return result


def load_report_disbursements_sumamry(cmte_id, report_id, levin_account_id=None):
    """
    query db for report-wise disbursement data
    """
    result = {}
    result["voter_reg_disb_amount"] = 0
    result["voter_id_disb_amount"] = 0
    result["gotv_disb_amount"] = 0
    result["generic_campaign_disb_amount"] = 0
    result["other_disb"] = 0
    if not levin_account_id:
        _sql = """
            SELECT t1.transaction_type_identifier, COALESCE(sum(t1.expenditure_amount),0) as total_amt
            FROM public.sched_b t1
            WHERE t1.memo_code IS NULL
            AND t1.cmte_id = %s
            AND t1.report_id = %s
            AND t1.delete_ind is distinct from 'Y'
            AND substring(t1.transaction_type_identifier,1,6) = 'LEVIN_'
            GROUP BY t1.transaction_type_identifier
        """
    else:
        _sql = """
            SELECT t1.transaction_type_identifier, COALESCE(sum(t1.expenditure_amount),0) as total_amt
            FROM public.sched_b t1
            WHERE t1.memo_code IS NULL
            AND t1.cmte_id = %s
            AND t1.report_id = %s
            AND t1.levin_account_id = %s
            AND t1.delete_ind is distinct from 'Y'
            AND substring(t1.transaction_type_identifier,1,6) = 'LEVIN_'
            GROUP BY t1.transaction_type_identifier
        """

    try:
        logger.debug("loading LB data...")
        with connection.cursor() as cursor:
            if levin_account_id:
                cursor.execute(_sql, (cmte_id, report_id, levin_account_id))
            else:
                cursor.execute(_sql, (cmte_id, report_id))
            if cursor.rowcount:
                for row in cursor.fetchall():
                    if row[0] == "LEVIN_VOTER_REG":
                        result["voter_reg_disb_amount"] = row[1]
                    elif row[0] == "LEVIN_VOTER_ID":
                        result["voter_id_disb_amount"] = row[1]
                    elif row[0] == "LEVIN_GOTV":
                        result["gotv_disb_amount"] = row[1]
                    elif row[0] == "LEVIN_GEN":
                        result["generic_campaign_disb_amount"] = row[1]
                    elif row[0] == "LEVIN_OTH_DISB":
                        result["other_disb"] = row[1]
                    else:
                        pass
            result["total_disb_sub"] = (
                float(result["voter_reg_disb_amount"])
                + float(result["voter_id_disb_amount"])
                + float(result["gotv_disb_amount"])
                + float(result["generic_campaign_disb_amount"])
            )
            result["total_disb"] = float(result["other_disb"]) + float(
                result["total_disb_sub"]
            )
    except Exception as e:
        raise Exception(
            "Error happens when query and calcualte disbursements:" + str(e)
        )
    logger.debug("LB result:{}".format(result))
    return result


def load_report_receipts_summary(cmte_id, report_id, levin_account_id=None):
    """
    query db and caculcate the summary data for receipts:
    1. itemized receipts: line_number = 11AI
    2. non-itemized receipts: line_number = 11AII
    3. 1and2_total: itemized + non-itemized
    4. other receipts
    5. all_total: 3 + other
    """
    if not levin_account_id:
        _sql1 = """
            SELECT (CASE WHEN t1.aggregate_amt > 200 THEN 'Y' ELSE 'N' END) as item_ind, COALESCE(sum(contribution_amount),0) as total_amt
            FROM public.sched_a t1
            WHERE t1.memo_code IS NULL
            AND t1.cmte_id = %s
            AND t1.report_id = %s
            AND t1.delete_ind is distinct from 'Y'
            AND substring(transaction_type_identifier, 1, 6) = 'LEVIN_'
            AND t1.transaction_type_identifier != 'LEVIN_OTH_REC'
            GROUP BY item_ind
        """
        _sql2 = """
            SELECT COALESCE(sum(contribution_amount),0)
            FROM public.sched_a t1
            WHERE t1.memo_code IS NULL
            AND t1.cmte_id = %s
            AND t1.report_id = %s
            AND t1.delete_ind is distinct from 'Y'
            AND t1.transaction_type_identifier = 'LEVIN_OTH_REC'
        """
    else:
        _sql1 = """
            SELECT (CASE WHEN t1.aggregate_amt > 200 THEN 'Y' ELSE 'N' END) as item_ind, COALESCE(sum(contribution_amount),0) as total_amt
            FROM public.sched_a t1
            WHERE t1.memo_code IS NULL
            AND t1.cmte_id = %s
            AND t1.report_id = %s
            AND t1.levin_account_id = %s
            AND t1.delete_ind is distinct from 'Y'
            AND substring(transaction_type_identifier, 1, 6) = 'LEVIN_'
            AND t1.transaction_type_identifier != 'LEVIN_OTH_REC'
            GROUP BY item_ind
        """
        _sql2 = """
            SELECT COALESCE(sum(contribution_amount),0)
            FROM public.sched_a t1
            WHERE t1.memo_code IS NULL
            AND t1.cmte_id = %s
            AND t1.report_id = %s
            AND t1.levin_account_id = %s
            AND t1.delete_ind is distinct from 'Y'
            AND t1.transaction_type_identifier = 'LEVIN_OTH_REC'
        """

    logger.debug(
        "loading receipts summary: cmte_id {}, report_id {}".format(cmte_id, report_id)
    )
    result = {}
    result["item_receipts"] = 0
    result["unitem_receipts"] = 0
    try:
        with connection.cursor() as cursor:
            if levin_account_id:
                cursor.execute(_sql1, (cmte_id, report_id, levin_account_id))
            else:
                cursor.execute(_sql1, (cmte_id, report_id))
            logger.debug("rows retrieved:{}".format(cursor.rowcount))
            if cursor.rowcount:

                rows = cursor.fetchall()
                for row in rows:
                    if row[0] == "Y":
                        result["item_receipts"] = row[1]
                    elif row[0] == "N":
                        result["unitem_receipts"] = row[1]
                    else:
                        pass

            result["total_c_receipts"] = float(result["item_receipts"]) + float(
                result["unitem_receipts"]
            )

            logger.debug("loading other la transactions:")
            if levin_account_id:
                cursor.execute(_sql2, (cmte_id, report_id, levin_account_id))
            else:
                cursor.execute(_sql2, (cmte_id, report_id))
            if cursor.rowcount:
                result["other_receipts"] = cursor.fetchone()[0]
            else:
                result["other_receipts"] = 0
            result["total_receipts"] = float(result["total_c_receipts"]) + float(
                result["other_receipts"]
            )
            logger.debug("receipts summary:{}".format(result))
    except Exception as e:
        raise Exception(
            "Error happens when query and calcualte receipts amount:" + str(e)
        )
    return result


def get_cash_on_hand_cop(report_id, cmte_id, prev_yr, levin_account_id=None):
    """
    getting cash on hand at the beginning:
    it is loadind the closing coh value from the sched_l
    1. from previous report, report-based
    2. last report from previous year, year-based
    """
    try:
        logger.debug("****loading coh beginning data...")
        cvg_start_date, cvg_end_date = get_cvg_dates(report_id, cmte_id)
        if prev_yr:
            prev_cvg_year = cvg_start_date.year - 1
            prev_cvg_end_dt = datetime.date(prev_cvg_year, 12, 31)
        else:
            prev_cvg_end_dt = cvg_start_date - datetime.timedelta(days=1)
        with connection.cursor() as cursor:
            if levin_account_id:
                cursor.execute(
                    """
                    SELECT COALESCE(coh_cop, 0)
                    FROM public.sched_l
                    WHERE cmte_id = %s
                    AND cvg_end_date <= %s
                    AND record_id = %s::varchar(9)
                    AND delete_ind is distinct from 'Y'
                    ORDER BY cvg_end_date DESC
                    """,
                    [cmte_id, prev_cvg_end_dt, levin_account_id],
                )

            else:
                cursor.execute(
                    """
                    SELECT COALESCE(coh_cop, 0)
                    FROM public.sched_l
                    WHERE cmte_id = %s
                    AND cvg_end_date <= %s
                    AND delete_ind is distinct from 'Y'
                    ORDER BY cvg_end_date DESC, record_id ASC
                    """,
                    [cmte_id, prev_cvg_end_dt],
                )
            if cursor.rowcount == 0:
                coh_cop = 0
            else:
                result = cursor.fetchone()
                coh_cop = result[0]
                if not coh_cop:
                    coh_cop = 0
        logger.debug("coh result:{}".format(coh_cop))
        return float(coh_cop)
    except Exception as e:
        raise Exception(
            "The prev_cash_on_hand_cop function is throwing an error: " + str(e)
        )


#############


def load_ytd_disbursements_summary_api(
    cmte_id, start_dt, end_dt, levin_account_id=None
):
    """
    load year_to_date disbursement amount
    """
    result = {}
    result["voter_registration_disbursement_ytd"] = 0
    result["voter_ID_disbursement_ytd"] = 0
    result["GOTV_disbursement_ytd"] = 0
    result["generic_campaign_disbursement_ytd"] = 0
    result["other_disbursement_ytd"] = 0
    if levin_account_id:
        _sql = """
            SELECT t1.transaction_type_identifier, COALESCE(sum(t1.expenditure_amount),0) as total_amt
            FROM public.sched_b t1
            WHERE t1.memo_code IS NULL
            AND t1.cmte_id = %s
            AND t1.expenditure_date BETWEEN %s and %s
            AND t1.levin_account_id = %s
            AND t1.delete_ind is distinct from 'Y'
            AND substr(t1.transaction_type_identifier,1,6) = 'LEVIN_'
            GROUP BY t1.transaction_type_identifier
        """
    else:
        _sql = """
            SELECT t1.transaction_type_identifier, COALESCE(sum(t1.expenditure_amount),0) as total_amt
            FROM public.sched_b t1
            WHERE t1.memo_code IS NULL
            AND t1.cmte_id = %s
            AND t1.expenditure_date BETWEEN %s and %s
            AND t1.delete_ind is distinct from 'Y'
            AND substr(t1.transaction_type_identifier,1,6) = 'LEVIN_'
            GROUP BY t1.transaction_type_identifier
        """
    try:
        with connection.cursor() as cursor:
            if levin_account_id:
                cursor.execute(_sql, (cmte_id, start_dt, end_dt, levin_account_id))
            else:
                cursor.execute(_sql, (cmte_id, start_dt, end_dt))
            # rows = cursor.fetchall()
            if cursor.rowcount:
                for row in cursor.fetchall():
                    if row[0] == "LEVIN_VOTER_REG":
                        result["voter_registration_disbursement_ytd"] = row[1]
                    elif row[0] == "LEVIN_VOTER_ID":
                        result["voter_ID_disbursement_ytd"] = row[1]
                    elif row[0] == "LEVIN_GOTV":
                        result["GOTV_disbursement_ytd"] = row[1]
                    elif row[0] == "LEVIN_GEN":
                        result["generic_campaign_disbursement_ytd"] = row[1]
                    elif row[0] == "LEVIN_OTH_DISB":
                        result["other_disbursement_ytd"] = row[1]
                    else:
                        pass
            result["line4_subtotal_ytd"] = (
                float(result["voter_registration_disbursement_ytd"])
                + float(result["voter_ID_disbursement_ytd"])
                + float(result["GOTV_disbursement_ytd"])
                + float(result["generic_campaign_disbursement_ytd"])
            )
            result["total_disbursement_amount_ytd"] = float(
                result["other_disbursement_ytd"]
            ) + float(result["line4_subtotal_ytd"])
    except Exception as e:
        raise Exception(
            "Error happens when query and calcualte dsibursements:" + str(e)
        )
    return result


def load_ytd_receipts_summary_api(cmte_id, start_dt, end_dt, levin_account_id=None):
    """
    load year_to_date receipt aggregation amount
    """
    result = {}
    result["itemized_receipt_amount_ytd"] = 0
    result["non_itemized_receipt_amount_ytd"] = 0
    result["other_sl_receipt_amount_ytd"] = 0

    if levin_account_id:
        _sql1 = """
            SELECT (CASE WHEN t1.aggregate_amt > 200 THEN 'Y' ELSE 'N' END) as item_ind, COALESCE(sum(contribution_amount),0) as total_amt
            FROM public.sched_a t1
            WHERE t1.memo_code IS NULL
            AND t1.cmte_id = %s
            AND t1.contribution_date BETWEEN %s AND %s
            AND t1.levin_account_id = %s
            AND t1.delete_ind is distinct from 'Y'
            AND substr(t1.transaction_type_identifier,1,5) = 'LEVIN'
            AND t1.transaction_type_identifier != 'LEVIN_OTH_REC'
            GROUP BY item_ind
        """

        _sql2 = """
            SELECT COALESCE(sum(contribution_amount),0)
            FROM public.sched_a t1
            WHERE t1.memo_code IS NULL
            AND t1.cmte_id = %s
            AND t1.contribution_date BETWEEN %s AND %s
            AND t1.levin_account_id = %s
            AND t1.delete_ind is distinct from 'Y'
            AND transaction_type_identifier = 'LEVIN_OTH_REC'
        """

    else:
        _sql1 = """
            SELECT (CASE WHEN t1.aggregate_amt > 200 THEN 'Y' ELSE 'N' END) as item_ind, COALESCE(sum(contribution_amount),0) as total_amt
            FROM public.sched_a t1
            WHERE t1.memo_code IS NULL
            AND t1.cmte_id = %s
            AND t1.contribution_date BETWEEN %s AND %s
            AND t1.delete_ind is distinct from 'Y'
            AND substr(t1.transaction_type_identifier,1,5) = 'LEVIN'
            AND t1.transaction_type_identifier != 'LEVIN_OTH_REC'
            GROUP BY item_ind
        """

        _sql2 = """
            SELECT COALESCE(sum(contribution_amount),0)
            FROM public.sched_a t1
            WHERE t1.memo_code IS NULL
            AND t1.cmte_id = %s
            AND t1.contribution_date BETWEEN %s AND %s
            AND t1.delete_ind is distinct from 'Y'
            AND transaction_type_identifier = 'LEVIN_OTH_REC'
        """

    try:
        with connection.cursor() as cursor:
            if levin_account_id:
                cursor.execute(_sql1, (cmte_id, start_dt, end_dt, levin_account_id))
            else:
                cursor.execute(_sql1, (cmte_id, start_dt, end_dt))
            if cursor.rowcount:
                rows = cursor.fetchall()
                for row in rows:
                    if row[0] == "Y":
                        result["itemized_receipt_amount_ytd"] = row[1]
                    elif row[0] == "N":
                        result["non_itemized_receipt_amount_ytd"] = row[1]
                    else:
                        pass
            result["itemized_non_itemized_combined_ytd"] = float(
                result["itemized_receipt_amount_ytd"]
            ) + float(result["non_itemized_receipt_amount_ytd"])

            if levin_account_id:
                cursor.execute(_sql2, (cmte_id, start_dt, end_dt, levin_account_id))
            else:
                cursor.execute(_sql2, (cmte_id, start_dt, end_dt))
            if cursor.rowcount:
                result["other_sl_receipt_amount_ytd"] = cursor.fetchone()[0]

            result["total_receipt_amount_ytd"] = float(
                result["itemized_non_itemized_combined_ytd"]
            ) + float(result["other_sl_receipt_amount_ytd"])

    except Exception as e:
        raise Exception("Error happens when query ytd receipts amount:" + str(e))
    return result


def load_report_disbursements_sumamry_api(cmte_id, report_id, levin_account_id=None):
    """
    query db for report-wise disbursement data
    """
    result = {}
    result["voter_registration_disbursement"] = 0
    result["voter_ID_disbursement"] = 0
    result["GOTV_disbursement"] = 0
    result["generic_campaign_disbursement"] = 0
    result["other_disbursement"] = 0
    if not levin_account_id:
        _sql = """
            SELECT t1.transaction_type_identifier, COALESCE(sum(t1.expenditure_amount),0) as total_amt
            FROM public.sched_b t1
            WHERE t1.memo_code IS NULL
            AND t1.cmte_id = %s
            AND t1.report_id = %s
            AND t1.delete_ind is distinct from 'Y'
            AND substring(t1.transaction_type_identifier,1,6) = 'LEVIN_'
            GROUP BY t1.transaction_type_identifier
        """
    else:
        _sql = """
            SELECT t1.transaction_type_identifier, COALESCE(sum(t1.expenditure_amount),0) as total_amt
            FROM public.sched_b t1
            WHERE t1.memo_code IS NULL
            AND t1.cmte_id = %s
            AND t1.report_id = %s
            AND t1.levin_account_id = %s
            AND t1.delete_ind is distinct from 'Y'
            AND substring(t1.transaction_type_identifier,1,6) = 'LEVIN_'
            GROUP BY t1.transaction_type_identifier
        """

    try:
        with connection.cursor() as cursor:
            if levin_account_id:
                cursor.execute(_sql, (cmte_id, report_id, levin_account_id))
            else:
                cursor.execute(_sql, (cmte_id, report_id))
            for row in cursor.fetchall():
                if row[0] == "LEVIN_VOTER_REG":
                    result["voter_registration_disbursement"] = row[1]
                elif row[0] == "LEVIN_VOTER_ID":
                    result["voter_ID_disbursement"] = row[1]
                elif row[0] == "LEVIN_GOTV":
                    result["GOTV_disbursement"] = row[1]
                elif row[0] == "LEVIN_GEN":
                    result["generic_campaign_disbursement"] = row[1]
                elif row[0] == "LEVIN_OTH_DISB":
                    result["other_disbursement"] = row[1]
                else:
                    pass
            result["line4_subtotal"] = (
                float(result["voter_registration_disbursement"])
                + float(result["voter_ID_disbursement"])
                + float(result["GOTV_disbursement"])
                + float(result["generic_campaign_disbursement"])
            )
            result["total_disbursement_amount"] = float(
                result["other_disbursement"]
            ) + float(result["line4_subtotal"])
    except Exception as e:
        raise Exception(
            "Error happens when query and calcualte disbursements:" + str(e)
        )
    return result


def load_report_receipts_summary_api(cmte_id, report_id, levin_account_id=None):
    """
    query db and caculcate the summary data for receipts:
    1. itemized receipts: line_number = 11AI
    2. non-itemized receipts: line_number = 11AII
    3. 1and2_total: itemized + non-itemized
    4. other receipts
    5. all_total: 3 + other
    """
    if not levin_account_id:
        _sql1 = """
            SELECT (CASE WHEN t1.aggregate_amt > 200 THEN 'Y' ELSE 'N' END) as item_ind, COALESCE(sum(contribution_amount),0) as total_amt
            FROM public.sched_a t1
            WHERE t1.memo_code IS NULL
            AND t1.cmte_id = %s
            AND t1.report_id = %s
            AND t1.delete_ind is distinct from 'Y'
            AND substring(transaction_type_identifier, 1, 6) = 'LEVIN_'
            AND t1.transaction_type_identifier != 'LEVIN_OTH_REC'
            GROUP BY item_ind
        """
        _sql2 = """
            SELECT COALESCE(sum(contribution_amount),0)
            FROM public.sched_a t1
            WHERE t1.memo_code IS NULL
            AND t1.cmte_id = %s
            AND t1.report_id = %s
            AND t1.delete_ind is distinct from 'Y'
            AND t1.transaction_type_identifier = 'LEVIN_OTH_REC'
        """
    else:
        _sql1 = """
            SELECT (CASE WHEN t1.aggregate_amt > 200 THEN 'Y' ELSE 'N' END) as item_ind, COALESCE(sum(contribution_amount),0) as total_amt
            FROM public.sched_a t1
            WHERE t1.memo_code IS NULL
            AND t1.cmte_id = %s
            AND t1.report_id = %s
            AND t1.levin_account_id = %s
            AND t1.delete_ind is distinct from 'Y'
            AND substring(transaction_type_identifier, 1, 6) = 'LEVIN_'
            AND t1.transaction_type_identifier != 'LEVIN_OTH_REC'
            GROUP BY item_ind
        """
        _sql2 = """
            SELECT COALESCE(sum(contribution_amount),0)
            FROM public.sched_a t1
            WHERE t1.memo_code IS NULL
            AND t1.cmte_id = %s
            AND t1.report_id = %s
            AND t1.levin_account_id = %s
            AND t1.delete_ind is distinct from 'Y'
            AND t1.transaction_type_identifier = 'LEVIN_OTH_REC'
        """

    logger.debug(
        "loading receipts summary: cmte_id {}, report_id {}".format(cmte_id, report_id)
    )
    result = {}
    result["itemized_receipt_amount"] = 0
    result["non_itemized_receipt_amount"] = 0
    try:
        with connection.cursor() as cursor:
            if levin_account_id:
                cursor.execute(_sql1, (cmte_id, report_id, levin_account_id))
            else:
                cursor.execute(_sql1, (cmte_id, report_id))
            logger.debug("rows retrieved:{}".format(cursor.rowcount))
            if cursor.rowcount:

                rows = cursor.fetchall()
                for row in rows:
                    if row[0] == "Y":
                        result["itemized_receipt_amount"] = row[1]
                    elif row[0] == "N":
                        result["non_itemized_receipt_amount"] = row[1]
                    else:
                        pass

            result["itemized_non_itemized_combined"] = float(
                result["itemized_receipt_amount"]
            ) + float(result["non_itemized_receipt_amount"])

            logger.debug("loading other la transactions:")
            if levin_account_id:
                cursor.execute(_sql2, (cmte_id, report_id, levin_account_id))
            else:
                cursor.execute(_sql2, (cmte_id, report_id))
            if cursor.rowcount:
                result["other_sl_receipt_amount"] = cursor.fetchone()[0]
            else:
                result["other_sl_receipt_amount"] = 0
            result["total_receipt_amount"] = float(
                result["itemized_non_itemized_combined"]
            ) + float(result["other_sl_receipt_amount"])
            logger.debug("receipts summary:{}".format(result))
    except Exception as e:
        raise Exception(
            "Error happens when query and calcualte receipts amount:" + str(e)
        )
    return result


@api_view(["GET"])
def get_sl_summary_table(request):
    """
    report-based summary:
    values to be calculated:
    Receipts
    1. itemized receipts: line_number = 1A, amt > 200
    2. non-itemized receipts: line_number = 1A, amt <= 200
    3. 1and2_total: itemized + non-itemized
    4. other receipts
    5. all_total: 3 + other

    disbursements: transfer to federal acct or aalocation acct
    1. voter registration
    2. voter id;
    3. GOTV
    4. generic_campaign
    5. 1_2_3_4_total

    cash_on_hand:
    1. COH at the beginning
    2. receipts total
    3. sub_total: 1+2
    4. dsibursements total
    5. ending COH

    we also need a copy of YTD calculation for the same fields
    """
    response = {}
    try:
        cmte_id = get_comittee_id(request.user.username)

        if not (
            "report_id" in request.query_params
            and check_null_value(request.query_params.get("report_id"))
        ):
            raise Exception("Missing Input: report_id is mandatory")

        if not (
            "calendar_year" in request.query_params
            and check_null_value(request.query_params.get("calendar_year"))
        ):
            raise Exception("Missing Input: calendar_year is mandatory")

        report_id = check_report_id(request.query_params.get("report_id"))
        # calendar_year = check_calendar_year(request.query_params.get("calendar_year"))

        # period_args = [
        # cal_end = (datetime.date(int(calendar_year), 12, 31),)
        cvg_start_date, cvg_end_date = get_cvg_dates(report_id, cmte_id)
        cal_end = cvg_end_date
        calendar_year = cvg_start_date.year
        cal_start = (datetime.date(int(calendar_year), 1, 1),)
        # cmte_id,
        # report_id,
        # ]
        # query and calculate receipt amount for current report
        levin_account_id = request.query_params.get("levin_account_id")
        if levin_account_id:
            response.update(
                load_report_receipts_summary_api(cmte_id, report_id, levin_account_id)
            )
            response.update(
                load_report_disbursements_sumamry_api(
                    cmte_id, report_id, levin_account_id
                )
            )
            response.update(
                load_ytd_receipts_summary_api(
                    cmte_id, cal_start, cal_end, levin_account_id
                )
            )
            response.update(
                load_ytd_disbursements_summary_api(
                    cmte_id, cal_start, cal_end, levin_account_id
                )
            )
            coh_bop_report = get_cash_on_hand_cop(
                report_id, cmte_id, False, levin_account_id
            )
            coh_bop_ytd = get_cash_on_hand_cop(
                report_id, cmte_id, True, levin_account_id
            )
        else:
            response.update(load_report_receipts_summary_api(cmte_id, report_id))
            response.update(load_report_disbursements_sumamry_api(cmte_id, report_id))
            response.update(load_ytd_receipts_summary_api(cmte_id, cal_start, cal_end))
            response.update(
                load_ytd_disbursements_summary_api(cmte_id, cal_start, cal_end)
            )
            coh_bop_report = get_cash_on_hand_cop(report_id, cmte_id, False)
            coh_bop_ytd = get_cash_on_hand_cop(report_id, cmte_id, True)

        coh_cop_report = (
            coh_bop_report
            + response.get("total_receipt_amount")
            - response.get("total_disbursement_amount")
        )
        coh_cop_ytd = (
            coh_bop_ytd
            + response.get("total_receipt_amount_ytd")
            - response.get("total_disbursement_amount_ytd")
        )
        cash_summary = {
            "coh_bop_report": coh_bop_report,
            "coh_bop_ytd": coh_bop_ytd,
            "coh_cop_report": coh_cop_report,
            "coh_cop_ytd": coh_cop_ytd,
        }
        response.update(cash_summary)
        subtotal_report = float(response.get("coh_bop_report")) + float(
            response.get("total_receipt_amount")
        )
        subtotal_ytd = float(response.get("coh_bop_ytd")) + float(
            response.get("total_receipt_amount_ytd")
        )
        # adding subtotal numbers
        response.update(
            {"subtotal_report": subtotal_report, "subtotal_ytd": subtotal_ytd}
        )
        return Response(response, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            "The get_sl_summary_table API is throwing an error: " + str(e),
            status=status.HTTP_400_BAD_REQUEST,
        )


def get_sl_transaction_id(cmte_id, report_id, levin_account_id):
    """
    helper function for loading existing transaction_id if exist
    """
    try:
        _sql = """
        SELECT transaction_id
        FROM public.sched_l sl
        WHERE sl.cmte_id = %s
        AND sl.report_id = %s
        AND sl.record_id = %s::varchar(9)
        AND sl.delete_ind is distinct from 'Y'
        """
        with connection.cursor() as cursor:
            cursor.execute(_sql, [cmte_id, report_id, levin_account_id])
            if cursor.rowcount:
                return cursor.fetchone()[0]
            else:
                return None
    except BaseException:
        raise


def update_sl_summary(data):
    """
    report-based summary:
    values to be calculated:
    Receipts
    1. itemized receipts: line_number = 1A, amt > 200
    2. non-itemized receipts: line_number = 1A, amt <= 200
    3. 1and2_total: itemized + non-itemized
    4. other receipts
    5. all_total: 3 + other

    disbursements: transfer to federal acct or aalocation acct
    1. voter registration
    2. voter id;
    3. GOTV
    4. generic_campaign
    5. 1_2_3_4_total

    cash_on_hand:
    1. COH at the beginning
    2. receipts total
    3. sub_total: 1+2
    4. dsibursements total
    5. ending COH

    we also need a copy of YTD calculation for the same fields
    """
    logger.debug("update levin summary ...")
    logger.debug("with data:{}".format(data))
    try:
        cmte_id = data.get("cmte_id")
        original_report_id = data.get("report_id")
        levin_account_id = data.get("levin_account_id")

        cvg_start_date, cvg_end_date = get_cvg_dates(original_report_id, cmte_id)
        calendar_year = cvg_start_date.year
        cal_start = (datetime.date(int(calendar_year), 1, 1),)
        report_id_list = get_report_ids(cmte_id, cvg_start_date, False, True)
        # create a levin summary recvord if not exist yet
        for report_id in report_id_list:
            sl_data = {}
            report_cvg_start_date, report_cvg_end_date = get_cvg_dates(
                report_id, cmte_id
            )
            dummy_data = {
                "cmte_id": cmte_id,
                "report_id": report_id,
                "record_id": levin_account_id,
                "account_name": get_levin_account(cmte_id, levin_account_id)[0][
                    "levin_account_name"
                ],
                "cvg_from_date": report_cvg_start_date,
                "cvg_end_date": report_cvg_end_date,
                "transaction_type_identifier": "SCHED_L_SUM",
            }
            sl_data.update(dummy_data)

            logger.debug("sl_data {} for report id: {}".format(sl_data, report_id))
            # if levin_account_id:
            sl_data.update(
                load_report_receipts_summary(cmte_id, report_id, levin_account_id)
            )
            sl_data.update(
                load_report_disbursements_sumamry(cmte_id, report_id, levin_account_id)
            )
            sl_data.update(
                load_ytd_receipts_summary(
                    cmte_id, cal_start, report_cvg_end_date, levin_account_id
                )
            )
            sl_data.update(
                load_ytd_disbursements_summary(
                    cmte_id, cal_start, report_cvg_end_date, levin_account_id
                )
            )
            coh_bop_report = get_cash_on_hand_cop(
                report_id, cmte_id, False, levin_account_id
            )
            coh_bop_ytd = get_cash_on_hand_cop(
                report_id, cmte_id, True, levin_account_id
            )

            coh_cop_report = (
                coh_bop_report
                + float(sl_data.get("total_receipts"))
                - float(sl_data.get("total_disb"))
            )
            logger.debug("coh_cop_report:{}".format(coh_cop_report))
            coh_cop_ytd = (
                coh_bop_ytd
                + float(sl_data.get("total_receipts_ytd"))
                - float(sl_data.get("total_disb_ytd"))
            )
            logger.debug("coh_cop_ytd:{}".format(coh_cop_ytd))
            cash_summary = {
                "coh_bop": coh_bop_report,
                "coh_coy": coh_bop_ytd,
                "coh_cop": coh_cop_report,
                "coh_cop_ytd": coh_cop_ytd,
            }
            sl_data.update(cash_summary)
            logger.debug("sl_data after calculation:{}".format(sl_data))
            sl_data = schedL_sql_dict(sl_data)
            logger.debug("sl data after screening:{}".format(sl_data))
            transaction_id = get_sl_transaction_id(cmte_id, report_id, levin_account_id)
            if not transaction_id:
                if int(report_id) == int(original_report_id):
                    logger.debug("no transaction_id found. Saving a new record.")
                    post_schedL(sl_data)
            else:
                logger.debug("sl transaction_id identified:{}".format(transaction_id))
                sl_data["transaction_id"] = transaction_id
                put_schedL(sl_data)
                # sl_data.update({'transaction_id':})
            logger.debug("update sl done.")

    except BaseException:
        raise


def get_la_memos(cmte_id, report_id, transaction_id):
    """
    load child memo transactions for levin sched_a
    """
    return get_sched_a_transactions(
        report_id, cmte_id, back_ref_transaction_id=transaction_id
    )


@api_view(["GET"])
def get_sla_summary_table(request):
    """
    get all Levin sched_a summary for current report
    """
    # response = {}
    logger.debug("get_sql_summary with data:{}".format(request.query_params))

    try:

        #: Get the request parameters and set for Pagination
        query_params = request.query_params
        page_num = get_int_value(query_params.get("page"))

        itemsperpage = get_int_value(query_params.get("itemsPerPage"))
        cmte_id = get_comittee_id(request.user.username)

        if not (
            "report_id" in request.query_params
            and check_null_value(request.query_params.get("report_id"))
        ):
            raise Exception("Missing Input: report_id is mandatory")

        _sql_p1 = """
        SELECT json_agg(t) FROM
        (
            SELECT a.*, l.levin_account_name, tp.tran_desc, e.first_name, e.last_name, e.entity_name, e.entity_type
            FROM public.sched_a a, public.levin_account l, public.entity e, public.ref_transaction_types tp
            WHERE a.cmte_id = %s
            AND a.report_id = %s
            AND a.back_ref_transaction_id is null
            AND a.levin_account_id = l.levin_account_id
            AND a.entity_id = e.entity_id
            AND a.transaction_type_identifier = tp.tran_identifier
            --AND a.transaction_type_identifier in ("""

        _sql_p2 = """)
            AND a.delete_ind is distinct from 'Y'
        ) t
        """

        report_id = check_report_id(request.query_params.get("report_id"))
        transaction_tps = ["'" + tp + "'" for tp in LA_TRANSACTIONS if "MEMO" not in tp]
        tps_str = ",".join(transaction_tps)
        logger.debug("cmte_id:{}, report_id:{}".format(cmte_id, report_id))
        logger.debug("transaction_types:{}".format(tps_str))

        tran_desc_dic = get_transaction_type_descriptions()
        with connection.cursor() as cursor:
            cursor.execute(_sql_p1 + tps_str + _sql_p2, [cmte_id, report_id])
            result = cursor.fetchone()[0]
            # adding memo child transactions
            if result:
                for obj in result:
                    obj.update(API_CALL_LA)
                    if obj.get("transaction_type_identifier") == "LEVIN_PARTN_REC":
                        memo_objs = get_la_memos(
                            cmte_id, obj.get("report_id"), obj.get("transaction_id")
                        )
                        if memo_objs:
                            for m_obj in memo_objs:
                                (
                                    levin_account_id,
                                    levin_account_name,
                                ) = load_levin_account_data(m_obj.get("transaction_id"))
                                m_obj["levin_account_id"] = levin_account_id
                                m_obj["levin_account_name"] = levin_account_name
                                m_obj["tran_desc"] = tran_desc_dic.get(
                                    "LEVIN_PARTN_MEMO"
                                )
                                m_obj.update(API_CALL_LA)

                            obj["child"] = memo_objs

        #: update for pagination
        json_result = get_pagination_dataset(result, itemsperpage, page_num)
        return Response(json_result, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            "The get_sla_summary_table API is throwing an error: " + str(e),
            status=status.HTTP_400_BAD_REQUEST,
        )


#: get the paginator page with other details like
def get_pagination_dataset(json_res, itemsperpage, page_num):
    if check_null_value(json_res) is False or json_res is None:
        json_result = {
            "items": "",
            "totalItems": "",
            "itemsPerPage": "",
            "pageNumber": "",
            "totalPages": "",
        }
        return json_result
    else:
        total_count = len(json_res)
        paginator = Paginator(json_res, itemsperpage)
        if paginator.num_pages < page_num:
            page_num = paginator.num_pages
        json_res = paginator.page(page_num)
        json_result = {
            "items": list(json_res),
            "totalItems": total_count,
            "itemsPerPage": itemsperpage,
            "pageNumber": page_num,
            "totalPages": paginator.num_pages,
        }
        return json_result


def get_int_value(num):
    if num is not None:
        num = int(num)
    else:
        num = 1
    return int(num)


def load_levin_account_data(transaction_id):
    """
    helper function for loading levin_acct info
    """
    _sql = """
    SELECT sa.levin_account_id, la.levin_account_name
    FROM public.sched_a sa, public.levin_account la
    WHERE sa.levin_account_id = la.levin_account_id
    and sa.transaction_id = %s
    and sa.delete_ind is distinct from 'Y'
    """
    with connection.cursor() as cursor:
        cursor.execute(_sql, [transaction_id])
        if cursor.rowcount:
            _levin = cursor.fetchone()
            return _levin[0], _levin[1]
        else:
            raise Exception("Error loading levin account.")


@api_view(["GET"])
def get_slb_summary_table(request):
    """
    get all Levin sched_b summary for current report
    """
    # response = {}
    logger.debug("get_sql_summary with data:{}".format(request.query_params))

    try:

        #: Get the request parameters and set for Pagination
        query_params = request.query_params
        page_num = get_int_value(query_params.get("page"))
        descending = query_params.get("descending")
        itemsperpage = get_int_value(query_params.get("itemsPerPage"))

        if str(descending).lower() == "true":
            descending = "DESC"
        else:
            descending = "ASC"

        cmte_id = get_comittee_id(request.user.username)

        if not (
            "report_id" in request.query_params
            and check_null_value(request.query_params.get("report_id"))
        ):
            raise Exception("Missing Input: report_id is mandatory")

        _sql_p1 = """
        SELECT json_agg(t) FROM
        (
            SELECT b.*, l.levin_account_name, tp.tran_desc, e.first_name, e.last_name, e.entity_name, e.entity_type
            FROM public.sched_b b, public.levin_account l, public.entity e, public.ref_transaction_types tp
            WHERE b.cmte_id = %s
            AND b.report_id = %s
            AND b.levin_account_id = l.levin_account_id
            AND b.entity_id = e.entity_id
            AND b.transaction_type_identifier = tp.tran_identifier
            AND b.transaction_type_identifier in ("""

        _sql_p2 = """)
            AND b.delete_ind is distinct from 'Y'
        ) t
        """

        report_id = check_report_id(request.query_params.get("report_id"))
        transaction_tps = ["'" + tp + "'" for tp in LB_TRANSACTIONS if "MEMO" not in tp]
        tps_str = ",".join(transaction_tps)
        logger.debug("cmte_id:{}, report_id:{}".format(cmte_id, report_id))
        logger.debug("transaction_types:{}".format(tps_str))
        with connection.cursor() as cursor:
            cursor.execute(_sql_p1 + tps_str + _sql_p2, [cmte_id, report_id])
            result = cursor.fetchone()[0]
            # adding memo child transactions
            if result:
                for obj in result:
                    obj.update(API_CALL_LB)

        #: update for pagination
        json_result = get_pagination_dataset(result, itemsperpage, page_num)
        return Response(json_result, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            "The get_slb_summary_table API is throwing an error: " + str(e),
            status=status.HTTP_400_BAD_REQUEST,
        )
