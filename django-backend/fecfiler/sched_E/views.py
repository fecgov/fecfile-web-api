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
)
from fecfiler.sched_A.views import get_next_transaction_id
from fecfiler.sched_D.views import do_transaction


# Create your views here.
logger = logging.getLogger(__name__)

MANDATORY_FIELDS_SCHED_E = ["cmte_id", "report_id", "transaction_id"]


def check_transaction_id(transaction_id):
    if not (transaction_id[0:2] == "SE"):
        raise Exception(
            "The Transaction ID: {} is not in the specified format."
            + "Transaction IDs start with SE characters".format(transaction_id)
        )
    return transaction_id


def check_mandatory_fields_se(data):
    """
    validate mandatory fields for sched_e item
    """
    try:
        errors = []
        for field in MANDATORY_FIELDS_SCHED_E:
            if not (field in data and check_null_value(data.get(field))):
                errors.append(field)
        if errors:
            raise Exception(
                """
                The following mandatory fields are required in order 
                to save data to schedE table: {}""".format(
                    ",".join(errors)
                )
            )
    except:
        raise


def schedE_sql_dict(data):
    """
    filter out valid fileds for sched_E
    """
    valid_fields = [
        "transaction_type_identifier",
        "transaction_id",
        "back_ref_transaction_id",
        "back_ref_sched_name",
        "payee_entity_id",
        "election_code",
        "election_other_desc",
        "dissemination_date",
        "expenditure_amount",
        "disbursement_date",
        "calendar_ytd_amount",
        "purpose",
        "category_code",
        "payee_cmte_id",
        "support_oppose_code",
        "so_cand_id",
        "so_cand_last_name",
        "so_cand_fist_name",
        "so_cand_middle_name",
        "so_cand_prefix",
        "so_cand_suffix",
        "so_cand_office",
        "so_cand_district",
        "so_cand_state",
        "completing_entity_id",
        "date_signed",
        "memo_code",
        "memo_text",
        "delete_ind",
        "create_date",
        "last_update_date",
        "line_number",
        "entity_type",  # entity data after this line
        "entity_name",
        "first_name",
        "last_name",
        "middle_name",
        "preffix",
        "suffix",
        "street_1",
        "street_2",
        "city",
        "state",
        "zip_code",
        "occupation",
        "employer",
        "ref_cand_cmte_id",
        "cand_office",
        "cand_office_state",
        "cand_office_district",
        "cand_election_year",
    ]
    try:
        return {k: v for k, v in data.items() if k in valid_fields}
    except:
        raise Exception("invalid request data.")


def put_schedE(data):
    """
    update sched_E item
    here we are assuming entity_id are always referencing something already in our DB
    """
    try:
        check_mandatory_fields_SE(data)
        # check_transaction_id(data.get('transaction_id'))
        try:
            put_sql_schedE(data)
        except Exception as e:
            raise Exception(
                "The put_sql_schedE function is throwing an error: " + str(e)
            )
        return data
    except:
        raise


def put_sql_schedE(data):
    """
    update a schedule_e item                    
            
    """
    _sql = """
    UPDATE public.sched_e
    SET transaction_type_identifier= %s,
        back_ref_transaction_id= %s,
        back_ref_sched_name= %s,
        payee_entity_id= %s,
        election_code= %s,
        election_other_desc= %s,
        dissemination_date= %s,
        expenditure_amount= %s,
        disbursement_date= %s,
        calendar_ytd_amount= %s,
        purpose= %s,
        category_code= %s,
        payee_cmte_id= %s,
        support_oppose_code= %s,
        so_cand_id= %s,
        so_cand_last_name= %s,
        so_cand_fist_name= %s,
        so_cand_middle_name= %s,
        so_cand_prefix= %s,
        so_cand_suffix= %s,
        so_cand_office= %s,
        so_cand_district= %s,
        so_cand_state= %s,
        completing_entity_id= %s,
        date_signed= %s,
        memo_code= %s,
        memo_text= %s,
        line_number= %s,
        last_update_date= %s,
    WHERE transaction_id = %s AND report_id = %s AND cmte_id = %s 
    AND delete_ind is distinct from 'Y';
    """
    _v = (
        data.get("transaction_type_identifier"),
        data.get("back_ref_transaction_id"),
        data.get("back_ref_sched_name"),
        data.get("payee_entity_id"),
        data.get("election_code"),
        data.get("election_other_desc"),
        data.get("dissemination_date"),
        data.get("expenditure_amount"),
        data.get("disbursement_date"),
        data.get("calendar_ytd_amount"),
        data.get("purpose"),
        data.get("category_code"),
        data.get("payee_cmte_id"),
        data.get("support_oppose_code"),
        data.get("so_cand_id"),
        data.get("so_cand_last_name"),
        data.get("so_cand_fist_name"),
        data.get("so_cand_middle_name"),
        data.get("so_cand_prefix"),
        data.get("so_cand_suffix"),
        data.get("so_cand_office"),
        data.get("so_cand_district"),
        data.get("so_cand_state"),
        data.get("completing_entity_id"),
        data.get("date_signed"),
        data.get("memo_code"),
        data.get("memo_text"),
        data.get("line_number"),
        datetime.datetime.now(),
        data.get("transaction_id"),
        data.get("report_id"),
        data.get("cmte_id"),
    )
    do_transaction(_sql, _v)


def validate_se_data(data):
    """
    validate sE json data
    """
    check_mandatory_fields_se(data)


def post_schedE(data):
    """
    function for handling POST request for se, need to:
    1. generatye new transaction_id
    2. validate data
    3. save data to db
    """
    try:
        # check_mandatory_fields_SA(datum, MANDATORY_FIELDS_SCHED_A)
        data["transaction_id"] = get_next_transaction_id("SE")
        print(data)
        validate_se_data(data)
        try:
            post_sql_schedE(data)
        except Exception as e:
            raise Exception(
                "The post_sql_schedE function is throwing an error: " + str(e)
            )
        return data
    except:
        raise


def post_sql_schedE(data):
    """
    create a new sched_e item in DB
    """
    try:
        _sql = """
        INSERT INTO public.sched_e (
            cmte_id,
            report_id,
            transaction_type_identifier,
            transaction_id,
            back_ref_transaction_id,
            back_ref_sched_name,
            payee_entity_id,
            election_code,
            election_other_desc,
            dissemination_date,
            expenditure_amount,
            disbursement_date,
            calendar_ytd_amount,
            purpose,
            category_code,
            payee_cmte_id,
            support_oppose_code,
            so_cand_id,
            so_cand_last_name,
            so_cand_fist_name,
            so_cand_middle_name,
            so_cand_prefix,
            so_cand_suffix,
            so_cand_office,
            so_cand_district,
            so_cand_state,
            completing_entity_id,
            date_signed,
            memo_code,
            memo_text,
            line_number,
            create_date
            )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s); 
        """
        _v = (
            data.get("cmte_id"),
            data.get("report_id"),
            data.get("transaction_type_identifier"),
            data.get("transaction_id"),
            data.get("back_ref_transaction_id"),
            data.get("back_ref_sched_name"),
            data.get("payee_entity_id"),
            data.get("election_code"),
            data.get("election_other_desc"),
            data.get("dissemination_date"),
            data.get("expenditure_amount"),
            data.get("disbursement_date"),
            data.get("calendar_ytd_amount"),
            data.get("purpose,"),
            data.get("category_code"),
            data.get("payee_cmte_id"),
            data.get("support_oppose_code"),
            data.get("so_cand_id"),
            data.get("so_cand_last_name"),
            data.get("so_cand_fist_name"),
            data.get("so_cand_middle_name"),
            data.get("so_cand_prefix"),
            data.get("so_cand_suffix"),
            data.get("so_cand_office"),
            data.get("so_cand_district"),
            data.get("so_cand_state"),
            data.get("completing_entity_id"),
            data.get("date_signed"),
            data.get("memo_code"),
            data.get("memo_text"),
            data.get("line_number"),
            datetime.datetime.now(),
        )
        with connection.cursor() as cursor:
            # Insert data into schedD table
            cursor.execute(_sql, _v)
    except Exception:
        raise


def get_schedE(data):
    """
    load sched_e data based on cmte_id, report_id and transaction_id
    """
    try:
        cmte_id = data.get("cmte_id")
        report_id = data.get("report_id")
        if "transaction_id" in data:
            transaction_id = check_transaction_id(data.get("transaction_id"))
            forms_obj = get_list_schedE(report_id, cmte_id, transaction_id)
        else:
            forms_obj = get_list_all_schedE(report_id, cmte_id)
        return forms_obj
    except:
        raise


def get_list_all_schedE(report_id, cmte_id):
    """
    get all sched_e items for a report
    """
    try:
        with connection.cursor() as cursor:
            # GET single row from schedA table
            _sql = """SELECT json_agg(t) FROM ( SELECT
            cmte_id,
            report_id,
            transaction_type_identifier,
            transaction_id,
            back_ref_transaction_id,
            back_ref_sched_name,
            payee_entity_id,
            election_code,
            election_other_desc,
            dissemination_date,
            expenditure_amount,
            disbursement_date,
            calendar_ytd_amount,
            purpose,
            category_code,
            payee_cmte_id,
            support_oppose_code,
            so_cand_id,
            so_cand_last_name,
            so_cand_fist_name,
            so_cand_middle_name,
            so_cand_prefix,
            so_cand_suffix,
            so_cand_office,
            so_cand_district,
            so_cand_state,
            completing_entity_id,
            date_signed,
            memo_code,
            memo_text,
            line_number,
            create_date, 
            last_update_date
            FROM public.sched_e
            WHERE report_id = %s AND cmte_id = %s
            AND delete_ind is distinct from 'Y') t
            """
            cursor.execute(_sql, (report_id, cmte_id))
            schedE_list = cursor.fetchone()[0]
            if schedE_list is None:
                raise NoOPError(
                    "No sched_E transaction found for report_id {} and cmte_id: {}".format(
                        report_id, cmte_id
                    )
                )
            merged_list = []
            for dictE in schedE_list:
                merged_list.append(dictE)
        return merged_list
    except Exception:
        raise


def get_list_schedE(report_id, cmte_id, transaction_id):
    """
    get one sched_e item with tran_id
    """
    try:
        with connection.cursor() as cursor:
            # GET single row from schedA table
            _sql = """SELECT json_agg(t) FROM ( SELECT
            cmte_id,
            report_id,
            transaction_type_identifier,
            transaction_id,
            back_ref_transaction_id,
            back_ref_sched_name,
            payee_entity_id,
            election_code,
            election_other_desc,
            dissemination_date,
            expenditure_amount,
            disbursement_date,
            calendar_ytd_amount,
            purpose,
            category_code,
            payee_cmte_id,
            support_oppose_code,
            so_cand_id,
            so_cand_last_name,
            so_cand_fist_name,
            so_cand_middle_name,
            so_cand_prefix,
            so_cand_suffix,
            so_cand_office,
            so_cand_district,
            so_cand_state,
            completing_entity_id,
            date_signed,
            memo_code,
            memo_text,
            line_number,
            create_date, 
            last_update_date
            FROM public.sched_e
            WHERE report_id = %s AND cmte_id = %s AND transaction_id = %s
            AND delete_ind is distinct from 'Y') t
            """
            cursor.execute(_sql, (report_id, cmte_id, transaction_id))
            schedE_list = cursor.fetchone()[0]
            if schedE_list is None:
                raise NoOPError(
                    "No sched_e transaction found for transaction_id {}".format(
                        transaction_id
                    )
                )
            merged_list = []
            for dictE in schedE_list:
                merged_list.append(dictE)
        return merged_list
    except Exception:
        raise


def delete_sql_schedE(cmte_id, report_id, transaction_id):
    """
    do delete sql transaction
    """
    _sql = """
    UPDATE public.sched_e
    SET delete_ind = 'Y' 
    WHERE transaction_id = %s AND report_id = %s AND cmte_id = %s
    """
    _v = (transaction_id, report_id, cmte_id)
    do_transaction(_sql, _v)


def delete_schedE(data):
    """
    function for handling delete request for se
    """
    try:

        delete_sql_schedE(
            data.get("cmte_id"), data.get("report_id"), data.get("transaction_id")
        )
    except Exception as e:
        raise


@api_view(["POST", "GET", "DELETE", "PUT"])
def schedE(request):
    """
    this is the sched_e api
    """
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
            datum = schedE_sql_dict(request.data)
            datum["report_id"] = report_id
            datum["cmte_id"] = cmte_id
            if "transaction_id" in request.data and check_null_value(
                request.data.get("transaction_id")
            ):
                datum["transaction_id"] = check_transaction_id(
                    request.data.get("transaction_id")
                )
                data = put_schedE(datum)
            else:
                print(datum)
                data = post_schedE(datum)
            # Associating child transactions to parent and storing them to DB

            output = get_schedE(data)
            return JsonResponse(output[0], status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                "The schedE API - POST is throwing an exception: " + str(e),
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
            datum = get_schedE(data)
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
                "The schedE API - GET is throwing an error: " + str(e),
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
            delete_schedE(data)
            return Response(
                "The Transaction ID: {} has been successfully deleted".format(
                    data.get("transaction_id")
                ),
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return Response(
                "The schedE API - DELETE is throwing an error: " + str(e),
                status=status.HTTP_400_BAD_REQUEST,
            )

    elif request.method == "PUT":
        try:
            datum = schedE_sql_dict(request.data)
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
            datum["report_id"] = report_id
            datum["cmte_id"] = request.user.username

            data = put_schedE(datum)
            return JsonResponse(data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.debug(e)
            return Response(
                "The schedE API - PUT is throwing an error: " + str(e),
                status=status.HTTP_400_BAD_REQUEST,
            )

    else:
        raise NotImplementedError

