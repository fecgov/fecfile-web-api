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
from fecfiler.sched_A.views import (
    get_next_transaction_id,
    find_form_type,
    find_aggregate_date,
)
from fecfiler.sched_D.views import do_transaction


# Create your views here.
logger = logging.getLogger(__name__)

MANDATORY_FIELDS_SCHED_E = ["cmte_id", "report_id", "transaction_id"]
NEGATIVE_TRANSACTIONS = ["IE_VOID"]


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


def update_aggregate_on_transaction(
    cmte_id, report_id, transaction_id, aggregate_amount
):
    """
    update transaction with updated aggregate amount
    """
    print(transaction_id)
    print(aggregate_amount)
    try:
        _sql = """
        UPDATE public.sched_e
        SET calendar_ytd_amount= %s
        WHERE transaction_id = %s AND report_id = %s AND cmte_id = %s 
        AND delete_ind is distinct from 'Y'
        """
        do_transaction(_sql, (aggregate_amount, transaction_id, report_id, cmte_id))
    except Exception as e:
        raise Exception(
            """error on update aggregate amount
                        for transaction:{}""".format(
                transaction_id
            )
        )


def get_transactions_election_and_office(start_date, end_date, data):
    """
    load all transactions by electtion code and office within the date range.
    - for president election: election_code + office
    - for senate electtion: election_code + office + state
    - for house: election_code + office + state + district

    when both dissemination_date and disbursement_date are available, 
    we take priority on dissemination_date 
    """
    if data.get("so_cand_office") == "P":
        _sql = """
        SELECT  
                transaction_id, 
				expenditure_amount as transaction_amt,
				COALESCE(dissemination_date, disbursement_date) as transaction_dt
        FROM public.sched_e
        WHERE  
            cmte_id = %s
            AND COALESCE(dissemination_date, disbursement_date) >= %s
            AND COALESCE(dissemination_date, disbursement_date) <= %s
            AND election_code = %s
            AND delete_ind is distinct FROM 'Y' 
            ORDER BY transaction_dt ASC, create_date ASC;
        """
        _params = (data.get("cmte_id"), start_date, end_date, data.get("election_code"))
    elif data.get("so_cand_office") == "S":
        _sql = """
        SELECT  
                transaction_id, 
				expenditure_amount as transaction_amt,
				COALESCE(dissemination_date, disbursement_date) as transaction_dt
        FROM public.sched_e
        WHERE  
            cmte_id = %s
            AND COALESCE(dissemination_date, disbursement_date) >= %s
            AND COALESCE(dissemination_date, disbursement_date) <= %s
            AND election_code = %s
            AND so_cand_state = %s
            AND delete_ind is distinct FROM 'Y' 
            ORDER BY transaction_dt ASC, create_date ASC; 
        """
        _params = (
            data.get("cmte_id"),
            start_date,
            end_date,
            data.get("election_code"),
            data.get("so_cand_state"),
        )
    elif data.get("so_cand_office") == "H":
        _sql = """
        SELECT  
                transaction_id, 
				expenditure_amount as transaction_amt,
				COALESCE(dissemination_date, disbursement_date) as transaction_dt
        FROM public.sched_e
        WHERE  
            cmte_id = %s
            AND COALESCE(dissemination_date, disbursement_date) >= %s
            AND COALESCE(dissemination_date, disbursement_date) <= %s
            AND election_code = %s
            AND so_cand_state = %s
            AND so_cand_dsitrict = %s
            AND delete_ind is distinct FROM 'Y' 
            ORDER BY transaction_dt ASC, create_date ASC;  
        """
        _params = (
            data.get("cmte_id"),
            start_date,
            end_date,
            data.get("election_code"),
            data.get("so_cand_state"),
            data.get("so_cand_district"),
        )

    try:
        with connection.cursor() as cursor:
            cursor.execute(_sql, _params)
            transactions_list = cursor.fetchall()
        return transactions_list
    except Exception as e:
        raise Exception(
            "Getting transactions for election and office is throwing an error: "
            + str(e)
        )


def update_aggregate_amt_se(data):
    """
    update related se aggrgate amount
    
    """
    try:
        # itemization_value = 200
        cmte_id = data.get("cmte_id")
        report_id = data.get("report_id")
        form_type = find_form_type(report_id, cmte_id)
        # dissemination_date take priority
        if data.get("dissemination_date"):
            trans_dt = date_format(data.get("dissemination_date"))
        else:
            trans_dt = date_format(data.get("disbursement_date"))

        # if isinstance(contribution_date, str):
        # contribution_date = date_format(contribution_date)
        aggregate_start_date, aggregate_end_date = find_aggregate_date(
            form_type, trans_dt
        )
        # checking for child tranaction identifer for updating auto generated SB transactions
        # if transaction_type_identifier in AUTO_GENERATE_SCHEDB_PARENT_CHILD_TRANSTYPE_DICT.keys():
        #     child_flag = True
        #     child_transaction_type_identifier = AUTO_GENERATE_SCHEDB_PARENT_CHILD_TRANSTYPE_DICT.get(transaction_type_identifier)
        # make sure transaction list comes back sorted by contribution_date ASC
        # transactions_list = list_all_transactions_entity(
        #     aggregate_start_date,
        #     aggregate_end_date,
        #     transaction_type_identifier,
        #     entity_id,
        #     cmte_id,
        # )
        transaction_list = get_transactions_election_and_office(
            aggregate_start_date, aggregate_end_date, data
        )
        aggregate_amount = 0
        for transaction in transaction_list:
            aggregate_amount += transaction[1]
            logger.debug(
                "update aggregate amount for transaction:{}".format(transaction[0])
            )
            logger.debug("current aggregate amount:{}".format(aggregate_amount))
            update_aggregate_on_transaction(
                cmte_id, report_id, transaction[0], aggregate_amount
            )
            # # checking in reports table if the delete_ind flag is false for the corresponding report
            # if transaction[5] != 'Y':
            #     # checking if the back_ref_transaction_id is null or not.
            #     # If back_ref_transaction_id is none, checking if the transaction is a memo or not, using memo_code not equal to X.
            #     if (transaction[7]!= None or (transaction[7] == None and transaction[6] != 'X')):
            #         aggregate_amount += transaction[0]
            #     # Removed report_id constraint as we have to modify aggregate amount irrespective of report_id
            #     # if str(report_id) == str(transaction[2]):
            #     if contribution_date <= transaction[4]:
            #         line_number = get_linenumber_itemization(transaction_type_identifier, aggregate_amount, itemization_value, transaction[3])
            #         put_sql_linenumber_schedA(cmte_id, line_number, transaction[1], entity_id, aggregate_amount)

            #     #Updating aggregate amount to child auto generate sched B transactions
            #     if child_flag:
            #         child_SB_transaction_list = get_list_child_transactionId_schedB(cmte_id, transaction[1])
            #         for child_SB_transaction in child_SB_transaction_list:
            #             put_sql_agg_amount_schedB(cmte_id, child_SB_transaction[0], aggregate_amount)

    except Exception as e:
        raise Exception(
            "The update aggregate amount for sched_e is throwing an error: " + str(e)
        )


def validate_negative_transaction(data):
    """
    validate transaction amount if negative transaction encounterred.
    """
    if data.get("transaction_type_identifier") in NEGATIVE_TRANSACTIONS:
        if not float(data.get("expenditure_amount")) < 0:
            raise Exception("current transaction amount need to be negative!")


def post_schedE(data):
    """
    function for handling POST request for se, need to:
    1. generatye new transaction_id
    2. validate data
    3. save data to db
    """
    try:
        # check_mandatory_fields_SA(datum, MANDATORY_FIELDS_SCHED_A)
        logger.debug("saving sched_e with data:{}".format(data))
        if "payee_entity_id" in data:
            logger.debug("update payee entity with data:{}".format(data))
            get_data = {
                "cmte_id": data.get("cmte_id"),
                "entity_id": data.get("payee_entity_id"),
            }

            # need this update for FEC entity
            if get_data["entity_id"].startswith("FEC"):
                get_data["cmte_id"] = "C00000000"
            old_entity = get_entities(get_data)[0]
            new_entity = put_entities(data)
            rollback_flag = True
        else:
            logger.debug("saving new entity:{}".format(data))
            new_entity = post_entities(data)
            logger.debug("new entity created:{}".format(new_entity))
            rollback_flag = False

        # continue to save transaction
        entity_id = new_entity.get("entity_id")
        # print('post_scheda {}'.format(entity_id))
        data["payee_entity_id"] = entity_id
        data["transaction_id"] = get_next_transaction_id("SE")
        # print(data)
        validate_se_data(data)
        validate_negative_transaction(data)
        # TODO: add code for saving payee entity

        try:
            logger.debug("saving new sched_e item with data:{}".format(data))
            post_sql_schedE(data)
        except Exception as e:
            # remove entiteis if saving sched_a fails
            if rollback_flag:
                entity_data = put_entities(old_entity)
            else:
                get_data = {"cmte_id": data.get("cmte_id"), "entity_id": entity_id}
                remove_entities(get_data)
            raise Exception(
                "The post_sql_schedE function is throwing an error: " + str(e)
            )
        update_aggregate_amt_se(data)
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
        VALUES ({})
        """.format(
            ",".join(["%s"] * 32)
        )
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
        )
        logger.debug("sql:{}".format(_sql))
        logger.debug("parameters:{}".format(_v))
        with connection.cursor() as cursor:
            logger.info("sched_e db transaction: POST")
            # Insert data into schedD table
            cursor.execute(_sql, _v)
            logger.info("transaction done.")

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

