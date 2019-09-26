from django.shortcuts import render
import datetime
import json
import logging
import os
from decimal import Decimal

import requests
from django.conf import settings
from django.db import connection
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from fecfiler.core.views import (
    NoOPError,
    check_null_value,
    check_report_id,
    date_format,
    delete_entities,
    get_entities,
    post_entities,
    put_entities,
    remove_entities,
    undo_delete_entities,
    check_calendar_year,
)
from fecfiler.sched_A.views import get_next_transaction_id
from fecfiler.sched_D.views import do_transaction


# Create your views here.
logger = logging.getLogger(__name__)

MANDATORY_FIELDS_SCHED_L = ["cmte_id", "report_id", "transaction_id", "record_id"]


def check_transaction_id(transaction_id):
    if not (transaction_id[0:2] == "SL"):
        raise Exception(
            "The Transaction ID: {} is not in the specified format."
            + "Transaction IDs start with SL characters".format(transaction_id)
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
    except:
        raise


def schedL_sql_dict(data):
    """
    filter out valid fileds for sched_L

    """
    valid_fields = [
        "transaction_type_identifier",
        "line_number",
        "record_id",
        "account_name",
        "cvg_from_date",
        "cvg_end_date",
        "item_receipts",
        "unitem_receipts",
        "ttl_receipts",
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
        "total_reciepts_ytd",
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
        return {k: v for k, v in data.items() if k in valid_fields}
    except:
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
            put_sql_schedL(data)
        except Exception as e:
            raise Exception(
                "The put_sql_schedL function is throwing an error: " + str(e)
            )
        return data
    except:
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
                  ttl_receipts = %s,
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
                  total_reciepts_ytd = %s,
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
        data.get("ttl_receipts"),
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
        data.get("total_reciepts_ytd"),
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
        print(data)
        validate_sl_data(data)
        try:
            post_sql_schedL(data)
        except Exception as e:
            raise Exception(
                "The post_sql_schedL function is throwing an error: " + str(e)
            )
        return data
    except:
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
            ttl_receipts,
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
            total_reciepts_ytd,
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
            create_date ,
            last_update_date 
            )
        VALUES ({})
        """.format(
            ",".join(["%s"] * 45)
        )
        _v = (
            data.get("cmte_id"),
            data.get("report_id"),
            data.get("transaction_type_identifier"),
            data.get("line_number"),
            data.get("transaction_id"),
            data.get("record_id", ""),
            data.get("account_name", ""),
            data.get("cvg_from_date"),
            data.get("cvg_end_date"),
            data.get("item_receipts"),
            data.get("unitem_receipts"),
            data.get("ttl_receipts"),
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
            data.get("total_reciepts_ytd"),
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
    except:
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
            ttl_receipts,
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
            total_reciepts_ytd,
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
            for dictL in schedL_list:
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
            ttl_receipts,
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
            total_reciepts_ytd,
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
        raise


@api_view(["POST", "GET", "DELETE", "PUT"])
def schedL(request):

    if request.method == "POST":
        try:
            cmte_id = request.user.username
            if not ("report_id" in request.data):
                raise Exception("Missing Input: Report_id is mandatory")
            # handling null,none value of report_id
            if not (check_null_value(request.data.get("report_id"))):
                report_id = "0"
            else:
                report_id = check_report_id(request.data.get("report_id"))
            # end of handling
            datum = schedL_sql_dict(request.data)
            datum["report_id"] = report_id
            datum["cmte_id"] = cmte_id
            if "transaction_id" in request.data and check_null_value(
                request.data.get("transaction_id")
            ):
                datum["transaction_id"] = check_transaction_id(
                    request.data.get("transaction_id")
                )
                data = put_schedL(datum)
            else:
                print(datum)
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
            data = {"cmte_id": request.user.username}
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
            data = {"cmte_id": request.user.username}
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
            datum["cmte_id"] = request.user.username

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

    else:
        raise NotImplementedError


def load_ytd_disbursements_summary(cmte_id, start_dt, end_dt):
    """
    load year_to_date disbursement amount
    """
    result = {}
    _sql = """
        SELECT t1.transaction_type_identifier, COALESCE(sum(t1.expenditure_amount),0) as total_amt
        FROM public.sched_b t1 
        WHERE t1.memo_code IS NULL 
        AND t1.cmte_id = %s
        AND t1.expenditure_date BETWEEN %s and %s
        AND t1.delete_ind is distinct from 'Y' 
        AND t1.transaction_type_identifier like 'LEVIN_%'
        GROUP BY t1.transaction_type_identifier 
    """
    try:
        with connection.cursor() as cursor:
            # cursor.execute("SELECT line_number, contribution_amount FROM public.sched_a WHERE cmte_id = %s AND report_id = %s AND delete_ind is distinct from 'Y'", [cmte_id, report_id])
            cursor.execute(_sql, (cmte_id, report_id))
            # rows = cursor.fetchall()
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
                + float(result["voter_I_disbursement_ytd"])
                + float(result["GOTV_disbursement_ytd"])
                + float(result["generic__ytd"])
            )
    except Exception as e:
        raise Exception(
            "Error happens when query and calcualte dsibursements:" + str(e)
        )
    return result


def load_ytd_receipts_summary(cmte_id, start_dt, end_dt):
    """
    load year_to_date receipt aggregation amount
    """
    result = {}
    _sql1 = """
        SELECT line_number, COALESCE(sum(contribution_amount),0) as total_amt
        FROM public.sched_a t1 
        WHERE t1.memo_code IS NULL 
        AND t1.cmte_id = %s
        AND t1.contribution_date BETWEEN %s AND %s
        AND t1.delete_ind is distinct from 'Y' 
        AND transaction_type_identifier like 'LEVIN_%'
        GROUP BY line_number
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
            # cursor.execute("SELECT line_number, contribution_amount FROM public.sched_a WHERE cmte_id = %s AND report_id = %s AND delete_ind is distinct from 'Y'", [cmte_id, report_id])
            cursor.execute(_sql1, (cmte_id, start_dt, end_dt))
            rows = cursor.fetchall()
            for row in rows:
                if row[0] == "11AI":
                    result["itemized_receipt_amount_ytd"] = row[1]
                elif row[0] == "11AII":
                    result["non-itemized_receipt_amount_ytd"] = row[1]
                else:
                    pass
            result["itemized_non-itemized_combined_ytd"] = float(
                result["itemized_receipt_amount_ytd"]
            ) + float(result["non-itemized_receipt_amount_ytd"])
            cursor.execute(_sql2, (cmte_id, start_dt, end_dt))
            result["other_sl_receipt_amount_ytd"] = cursor.fetchone()[0]
            result["total_receipt_amount_ytd"] = float(
                result["itemized_non-itemized_combined"]
            ) + float(result["other_sl_receipt_amount"])

    except Exception as e:
        raise Exception("Error happens when query ytd receipts amount:" + str(e))

    return result


def load_report_disbursements_sumamry(cmte_id, report_id):
    """
    query db for report-wise disbursement data
    """
    result = {}
    _sql = """
        SELECT t1.transaction_type_identifier, COALESCE(sum(t1.expenditure_amount),0) as total_amt
        FROM public.sched_b t1 
        WHERE t1.memo_code IS NULL 
        AND t1.cmte_id = %s
        AND t1.report_id = %s
        AND t1.delete_ind is distinct from 'Y' 
        AND t1.transaction_type_identifier like 'LEVIN_%'
        GROUP BY t1.transaction_type_identifier
    """
    try:
        with connection.cursor() as cursor:
            # cursor.execute("SELECT line_number, contribution_amount FROM public.sched_a WHERE cmte_id = %s AND report_id = %s AND delete_ind is distinct from 'Y'", [cmte_id, report_id])
            cursor.execute(_sql, (cmte_id, report_id))
            # rows = cursor.fetchall()
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
                float(result["voter registration disbursement"])
                + float(result["voter ID disbursement"])
                + float(result["GOTV disbursement"])
                + float(result["generic campaign disbursement"])
            )
    except Exception as e:
        raise Exception(
            "Error happens when query and calcualte dsibursements:" + str(e)
        )
    return result


def load_report_receipts_sumamry(cmte_id, report_id):
    """
    query db and caculcate the summary data for receipts:
    1. itemized receipts: line_number = 11AI
    2. non-itemized receipts: line_number = 11AII
    3. 1and2_total: itemized + non-itemized
    4. other receipts
    5. all_total: 3 + other 
    """
    _sql1 = """
        SELECT line_number, COALESCE(sum(contribution_amount),0) as total_amt
        FROM public.sched_a t1 
        WHERE t1.memo_code IS NULL 
        AND t1.cmte_id = %s
        AND t1.report_id = %s
        AND t1.delete_ind is distinct from 'Y' 
        AND transaction_type_identifier like 'LEVIN_%'
        GROUP BY line_number
    """
    _sql2 = """
        SELECT COALESCE(sum(contribution_amount),0)
        FROM public.sched_a t1 
        WHERE t1.memo_code IS NULL 
        AND t1.cmte_id = %s
        AND t1.report_id = %s
        AND t1.delete_ind is distinct from 'Y' 
        AND transaction_type_identifier = 'LEVIN_OTH_REC'
    """
    result = {}
    try:
        with connection.cursor() as cursor:
            # cursor.execute("SELECT line_number, contribution_amount FROM public.sched_a WHERE cmte_id = %s AND report_id = %s AND delete_ind is distinct from 'Y'", [cmte_id, report_id])
            cursor.execute(_sql1, (cmte_id, report_id))
            rows = cursor.fetchall()
            for row in rows:
                if row[0] == "11AI":
                    result["itemized_receipt_amount"] = row[1]
                elif row[0] == "11AII":
                    result["non-itemized_receipt_amount"] = row[1]
                else:
                    pass
            result["itemized_non-itemized_combined"] = int(
                result["itemized_receipt_amount"]
            ) + int(result["non-itemized_receipt_amount"])
            cursor.execute(_sql2, (cmte_id, report_id))
            result["other_sl_receipt_amount"] = cursor.fetchone()[0]
            result["total_receipt_amount"] = int(
                result["itemized_non-itemized_combined"]
            ) + int(result["other_sl_receipt_amount"])

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
    1. itemized receipts: line_number = 11AI
    2. non-itemized receipts: line_number = 11AII
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
        cmte_id = request.user.username

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
        calendar_year = check_calendar_year(request.query_params.get("calendar_year"))

        # period_args = [
        cal_start = (datetime.date(int(calendar_year), 1, 1),)
        cal_end = (datetime.date(int(calendar_year), 12, 31),)
        # cmte_id,
        # report_id,
        # ]
        # query and calculate receipt amount for current report
        response.update(load_report_receipts_summary(cmte_id, report_id))

        # query and calculate disbursement amount for current report
        response.update(load_report_disbursements_sumamry(cmte_id, report_id))

        # query and calcualte YTD receipt amount
        response.update(load_ytd_receipts_summary(cmte_id, cal_start, cal_end))
        # query and calculate YTD disbursement amount
        response.update(load_ytd_disbursements_summary(cmte_id, cal_start, cal_end))

        """
        calendar_args = [cmte_id, date(int(calendar_year), 1, 1), date(int(calendar_year), 12, 31)]
        calendar_receipt = summary_receipts(calendar_args)
        calendar_disbursement = summary_disbursements(calendar_args)
        """
        # coh_bop_ytd = prev_cash_on_hand_cop(report_id, cmte_id, True)
        # coh_bop = prev_cash_on_hand_cop(report_id, cmte_id, False)
        # coh_cop = COH_cop(coh_bop, period_receipt, period_disbursement)

        # cash_summary = {
        #     "COH AS OF JANUARY 1": coh_bop_ytd,
        #     "BEGINNING CASH ON HAND": coh_bop,
        #     "ENDING CASH ON HAND": coh_cop,
        #     "DEBTS/LOANS OWED TO COMMITTEE": 0,
        #     "DEBTS/LOANS OWED BY COMMITTEE": 0,
        # }

        # forms_obj = {
        #     "Total Raised": {"period_receipts": period_receipt},
        #     "Total Spent": {"period_disbursements": period_disbursement},
        #     "Cash summary": cash_summary,
        # }
        forms_obj = {"dev_status": "partial"}
        return Response(forms_obj, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            "The get_sl_summary_table API is throwing an error: " + str(e),
            status=status.HTTP_400_BAD_REQUEST,
        )

