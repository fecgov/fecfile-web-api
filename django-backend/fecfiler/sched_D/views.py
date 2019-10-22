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

from fecfiler.core.transaction_util import (
    get_line_number_trans_type,
    get_sched_b_transactions,
    get_sched_f_child_transactions,
    get_sched_h4_child_transactions,
    get_sched_h6_child_transactions,
)

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

# from fecfiler.sched_B.views import (delete_parent_child_link_sql_schedB,
#                                     delete_schedB, get_list_child_schedB,
#                                     get_schedB, post_schedB, put_schedB,
#                                     schedB_sql_dict)

# Create your views here.
logger = logging.getLogger(__name__)

API_CALL_SB = {"api_call": "/sb/schedB"}
API_CALL_SF = {"api_call": "/sf/schedF"}
API_CALL_SH4 = {"api_call": "/sh4/schedH4"}
API_CALL_SH6 = {"api_call": "/sh6/schedH6"}

MANDATORY_FIELDS_SCHED_D = [
    "report_id",
    "cmte_id",
    "transaction_id",
    "transaction_type_identifier",
]
# Create your views here.


def check_transaction_id(transaction_id):
    try:
        # transaction_type_list = ["SD", ]
        # transaction_type = transaction_id[0:2]
        if not (transaction_id[0:2] == "SD"):
            raise Exception(
                """The Transaction ID: {} is not in the specified format. 
                Transaction IDs start with SD characters""".format(
                    transaction_id
                )
            )
        return transaction_id
    except Exception:
        raise


@api_view(["POST", "GET", "DELETE", "PUT"])
def schedD(request):
    """
    sched_a api supporting POST, GET, DELETE, PUT
    """

    # create new sched_d transaction
    if request.method == "POST":
        logger.debug("POST request received:{}".format(request.data))
        try:
            cmte_id = request.user.username
            if not ("report_id" in request.data):
                raise Exception("Missing Input: report_id is mandatory")
            # handling null,none value of report_id
            if not (check_null_value(request.data.get("report_id"))):
                report_id = "0"
            else:
                report_id = check_report_id(request.data.get("report_id"))
            # end of handling
            # save entoty first
            logger.debug("checking and filtering reqt data...")
            datum = schedD_sql_dict(request.data)
            logger.debug("valid data set:{}".format(datum))
            datum["report_id"] = report_id
            datum["cmte_id"] = cmte_id

            # if 'creditor_entity_id' in request.data and check_null_value(
            #         request.data.get('creditor_entity_id')):
            #     datum['creditor_entity_id'] = request.data.get(
            #         'creditor_entity_id')
            if "transaction_id" in request.data and check_null_value(
                request.data.get("transaction_id")
            ):
                datum["transaction_id"] = check_transaction_id(
                    request.data.get("transaction_id")
                )
                logger.debug(
                    "update transaction {} with data:{}".format(
                        datum.get("transaction_id", datum)
                    )
                )
                data = put_schedD(datum)
            else:
                logger.debug("saving new sd transaction:{}".format(datum))
                data = post_schedD(datum)
            # Associating child transactions to parent and storing them to DB

            output = get_schedD(data)
            return JsonResponse(output[0], status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                "The schedD API - POST is throwing an exception: " + str(e),
                status=status.HTTP_400_BAD_REQUEST,
            )

    elif request.method == "GET":
        try:
            data = {"cmte_id": request.user.username}
            if "report_id" in request.query_params:
                data["report_id"] = check_report_id(
                    request.query_params.get("report_id")
                )
            # elif "report_id" in request.query_params:
            #     data["report_id"] = check_report_id(
            #         request.query_params.get("report_id")
            #     )
            else:
                raise Exception("Missing Input: report_id is mandatory")
            if "transaction_id" in request.query_params and check_null_value(
                request.query_params.get("transaction_id")
            ):
                data["transaction_id"] = check_transaction_id(
                    request.query_params.get("transaction_id")
                )
            # if "transaction_id" in request.data and check_null_value(
            #     request.data.get("transaction_id")
            # ):
            #     data["transaction_id"] = check_transaction_id(
            #         request.data.get("transaction_id")
            #     )
            datum = get_schedD(data)
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
                "The schedD API - GET is throwing an error: " + str(e),
                status=status.HTTP_400_BAD_REQUEST,
            )

    elif request.method == "DELETE":
        try:
            data = {"cmte_id": request.user.username}
            if "report_id" in request.query_params:
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
            else:
                raise Exception("Missing Input: transaction_id is mandatory")
            delete_schedD(data)
            return Response(
                "The Transaction ID: {} has been successfully deleted".format(
                    data.get("transaction_id")
                ),
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return Response(
                "The schedD API - DELETE is throwing an error: " + str(e),
                status=status.HTTP_400_BAD_REQUEST,
            )

    elif request.method == "PUT":
        try:
            datum = schedD_sql_dict(request.data)
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
            data = put_schedD(datum)
            output = get_schedD(data)
            # output = get_schedA(data)
            return JsonResponse(output[0], status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.debug(e)
            return Response(
                "The schedD API - PUT is throwing an error: " + str(e),
                status=status.HTTP_400_BAD_REQUEST,
            )

    else:
        raise NotImplementedError


def delete_schedD(data):

    try:
        delete_sql_schedD(
            data.get("cmte_id"), data.get("report_id"), data.get("transaction_id")
        )
    except Exception as e:
        raise


def delete_sql_schedD(cmte_id, report_id, transaction_id):
    _sql = """UPDATE public.sched_d
    SET delete_ind = 'Y'
    WHERE transaction_id = %s AND report_id = %s AND cmte_id = %s;
    """
    _v = (transaction_id, report_id, cmte_id)
    do_transaction(_sql, _v)


def schedD_sql_dict(data):
    """
    filter data and build sched_d dictionary
    
    Note: those are fields from json data, not the fields in the db 
    table - they are not 100% match:
    like line_number, it is 'line_num' in db for now
    """
    valid_fields = [
        "transaction_type_identifier",
        "entity_id",
        "purpose",
        "beginning_balance",
        "incurred_amount",
        "payment_amount",
        "balance_at_close",
        "line_number",
        # entity_data
        "entity_id",
        "entity_type",
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
        "phone_number",
    ]
    try:
        valid_data = {k: v for k, v in data.items() if k in valid_fields}
        logger.debug("current valid data:{}".format(valid_data))
        line_num, tran_tp = get_line_number_trans_type(
            data["transaction_type_identifier"]
        )
        logger.debug(line_num)
        valid_data["line_number"] = line_num
        return valid_data
    except:
        raise Exception("invalid request data.")


def put_schedD(datum):
    """update sched_d item
    here we are assuming creditor_entoty_id are always referencing something already in our DB
    """
    try:
        # save entity data first
        if "entity_id" in datum:
            get_data = {
                "cmte_id": datum.get("cmte_id"),
                "entity_id": datum.get("entity_id"),
            }

            # need this update for FEC entity
            if get_data["entity_id"].startswith("FEC"):
                get_data["cmte_id"] = "C00000000"
            prev_entity_list = get_entities(get_data)
            entity_data = put_entities(datum)
            entity_flag = True
        else:
            entity_data = post_entities(datum)
            entity_flag = False

        # continue to save transaction
        entity_id = entity_data.get("entity_id")
        datum["entity_id"] = entity_id
        check_mandatory_fields_SD(datum)
        transaction_id = check_transaction_id(datum.get("transaction_id"))

        # flag = False
        # if 'entity_id' in datum:
        #     flag = True
        #     get_data = {
        #         'cmte_id': datum.get('cmte_id'),
        #         'entity_id': datum.get('entity_id')
        #     }
        #     prev_entity_list = get_entities(get_data)
        #     entity_data = put_entities(datum)
        # else:
        #     entity_data = post_entities(datum)
        # entity_id = entity_data.get('entity_id')
        # datum['entity_id'] = entity_id
        try:
            put_sql_schedD(datum)
        except Exception as e:
            if entity_flag:
                entity_data = put_entities(prev_entity_list[0])
            else:
                get_data = {"cmte_id": datum.get("cmte_id"), "entity_id": entity_id}
                remove_entities(get_data)
            raise Exception(
                "The put_sql_schedD function is throwing an error: " + str(e)
            )
        return datum
    except:
        raise


def check_mandatory_fields_SD(data):
    """
    validate mandatory fields for sched_a item
    """
    try:
        errors = []
        for field in MANDATORY_FIELDS_SCHED_D:
            if not (field in data and check_null_value(data.get(field))):
                errors.append(field)
        # if len(error) > 0:
        if errors:
            # string = ""
            # for x in error:
            #     string = string + x + ", "
            # string = string[0:-2]
            raise Exception(
                "The following mandatory fields are required in order to save data to schedD table: {}".format(
                    ",".join(errors)
                )
            )
    except:
        raise


def validate_sd_data(data):
    """
    validate: 1. mandatory sa fields; 2. valid line number and transaction types
    """
    check_mandatory_fields_SD(data)
    # validate_transaction_type(data)


def post_schedD(datum):
    """save sched_d item and the associated entities."""
    try:
        # check_mandatory_fields_SA(datum, MANDATORY_FIELDS_SCHED_A)
        if "entity_id" in datum:
            get_data = {
                "cmte_id": datum.get("cmte_id"),
                "entity_id": datum.get("entity_id"),
            }

            # need this update for FEC entity
            if get_data["entity_id"].startswith("FEC"):
                get_data["cmte_id"] = "C00000000"
            prev_entity_list = get_entities(get_data)
            entity_data = put_entities(datum)
            entity_flag = True
        else:
            entity_data = post_entities(datum)
            entity_flag = False

        # continue to save transaction
        entity_id = entity_data.get("entity_id")
        datum["entity_id"] = entity_id
        transaction_id = get_next_transaction_id("SD")
        datum["transaction_id"] = transaction_id
        validate_sd_data(datum)

        # save entities rirst
        # if 'creditor_entity_id' in datum:
        #     get_data = {
        #         'cmte_id': datum.get('cmte_id'),
        #         'entity_id': datum.get('creditor_entity_id')
        #     }
        #     prev_entity_list = get_entities(get_data)
        #     entity_data = put_entities(datum)
        # else:
        #     entity_data = post_entities(datum)

        # continue to save transaction
        # creditor_entity_id = entity_data.get('creditor_entity_id')
        # datum['creditor_entity_id'] = creditor_entity_id
        # datum['line_number'] = disclosure_rules(datum.get('line_number'), datum.get('report_id'), datum.get('transaction_type'), datum.get('contribution_amount'), datum.get('contribution_date'), entity_id, datum.get('cmte_id'))
        # trans_char = "SD"
        # transaction_id = get_next_transaction_id(trans_char)
        # datum['transaction_id'] = transaction_id
        try:
            post_sql_schedD(datum)
        except Exception as e:
            if entity_flag:
                entity_data = put_entities(prev_entity_list[0])
            else:
                get_data = {"cmte_id": datum.get("cmte_id"), "entity_id": entity_id}
                remove_entities(get_data)
            raise Exception(
                "The post_sql_schedD function is throwing an error: " + str(e)
            )
        return datum
    except:
        raise


def post_sql_schedD(data):
    try:
        _sql = """
        INSERT INTO public.sched_d (cmte_id,
                                    report_id,
                                    line_num,
                                    transaction_type_identifier,
                                    transaction_id,
                                    entity_id,
                                    purpose,
                                    beginning_balance,
                                    incurred_amount,
                                    payment_amount,
                                    balance_at_close,
                                    create_date)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);
        """
        _v = (
            data.get("cmte_id"),
            data.get("report_id"),
            data.get("line_number"),
            data.get("transaction_type_identifier"),
            data.get("transaction_id"),
            data.get("entity_id"),
            data.get("purpose"),
            data.get("beginning_balance"),
            data.get("incurred_amount"),
            data.get("payment_amount"),
            data.get("balance_at_close"),
            datetime.datetime.now(),
        )
        with connection.cursor() as cursor:
            # Insert data into schedD table
            cursor.execute(_sql, _v)
    except Exception:
        raise


def put_sql_schedD(data):
    """
    uopdate a schedule_d item
    """
    _sql = """UPDATE public.sched_d
            SET transaction_type_identifier = %s,
                line_num = %s,
                entity_id = %s,
                purpose = %s,
                beginning_balance = %s,
                balance_at_close = %s,
                incurred_amount = %s,
                payment_amount = %s,
                last_update_date = %s
            WHERE transaction_id = %s 
            AND report_id = %s 
            AND cmte_id = %s 
            AND delete_ind is distinct from 'Y';
        """
    _v = (
        data.get("transaction_type_identifier"),
        data.get("line_number"),
        data.get("entity_id"),
        data.get("purpose"),
        data.get("beginning_balance"),
        data.get("balance_at_close"),
        data.get("incurred_amount"),
        data.get("payment_amount"),
        datetime.datetime.now(),
        data.get("transaction_id"),
        data.get("report_id"),
        data.get("cmte_id"),
    )
    do_transaction(_sql, _v)


def do_transaction(sql, values):
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql, values)
            if cursor.rowcount == 0:
                raise Exception("The sql transaction: {} failed...".format(sql))
    except Exception:
        raise


def get_child_transactions(report_id, cmte_id, transaction_id):
    """
    adding all the pissible child transactions:
    sched_b, ached_e, sched_f, sched_h4, sched_h6
    TODO: need to add sched_e child data later on
    """

    sched_b_list = get_sched_b_transactions(
        report_id, cmte_id, back_ref_transaction_id=transaction_id
    )
    # TODO: will add all other transactions later on
    sched_f_list = get_sched_f_child_transactions(report_id, cmte_id, transaction_id)
    sched_h4_list = get_sched_h4_child_transactions(report_id, cmte_id, transaction_id)
    sched_h6_list = get_sched_h6_child_transactions(report_id, cmte_id, transaction_id)
    return sched_b_list + sched_f_list + sched_h4_list + sched_h6_list

    #     childA_forms_obj = get_list_child_schedA(
    #     report_id, cmte_id, transaction_id)
    # for obj in childA_forms_obj:
    #     obj.update(API_CALL_SA)
    #     obj.update({'election_year':REQ_ELECTION_YR})
    #     # obj.update(ELECTION_YR)

    # childB_forms_obj = get_list_child_schedB(
    #     report_id, cmte_id, transaction_id)
    # for obj in childB_forms_obj:
    #     obj.update(API_CALL_SB)
    #     obj.update({'election_year':REQ_ELECTION_YR})
    #     # obj.update(ELECTION_YR)

    # child_forms_obj = childA_forms_obj + childB_forms_obj
    # # for obj in childB_forms_obj:
    # #     obj.update({'api_call':''})


def get_schedD(data):
    """"
    load sched_d items
    """
    try:
        logger.debug("get_schedD with data:{}".format(data))
        cmte_id = data.get("cmte_id")
        report_id = data.get("report_id")
        if "transaction_id" in data:
            transaction_id = check_transaction_id(data.get("transaction_id"))
            forms_obj = get_list_schedD(report_id, cmte_id, transaction_id)
            child_objs = get_child_transactions(report_id, cmte_id, transaction_id)
            for obj in child_objs:  # this api_call code need to refactored later on
                if obj["transaction_id"].startswith("SB"):
                    obj.update(API_CALL_SB)
                if obj["transaction_id"].startswith("SF"):
                    obj.update(API_CALL_SF)
                if "levin_share" in obj:
                    obj.update(API_CALL_SH6)
                if "non_fed_share_amount" in obj:
                    obj.update(API_CALL_SH4)
            if len(child_objs) > 0:
                forms_obj[0]["child"] = child_objs
        else:
            forms_obj = get_list_all_schedD(report_id, cmte_id)
        return forms_obj
    except:
        raise


def get_list_all_schedD(report_id, cmte_id):
    """
    load sched_d items from DB
    """

    try:
        with connection.cursor() as cursor:
            # GET all rows from schedA table
            # GET single row from schedA table
            query_string = """
            SELECT cmte_id, 
                    report_id, 
                    line_num,
                    transaction_type_identifier, 
                    transaction_id, 
                    entity_id, 
                    beginning_balance, 
                    balance_at_close, 
                    incurred_amount, 
                    payment_amount, 
                    last_update_date
            FROM public.sched_d 
            WHERE report_id = %s 
            AND cmte_id = %s 
            AND delete_ind is distinct from 'Y'
            """

            cursor.execute(
                """SELECT json_agg(t) FROM (""" + query_string + """) t""",
                (report_id, cmte_id),
            )

            schedD_list = cursor.fetchone()[0]

            if schedD_list is None:
                raise NoOPError(
                    "The Report id:{} does not have any schedD transactions".format(
                        report_id
                    )
                )
            merged_list = []
            for dictD in schedD_list:
                entity_id = dictD.get("entity_id")
                q_data = {"entity_id": entity_id, "cmte_id": cmte_id}
                entity_list = get_entities(q_data)
                dictEntity = entity_list[0]
                # merged_dict = {**dictD, **dictEntity}
                merged_list.append({**dictD, **dictEntity})
        return merged_list
    except Exception:
        raise


def get_list_schedD(report_id, cmte_id, transaction_id):

    try:
        with connection.cursor() as cursor:
            # GET single row from schedA table
            query_string = """
            SELECT cmte_id,
                    report_id,
                    line_num,
                    transaction_type_identifier,
                    transaction_id,
                    entity_id,
                    beginning_balance,
                    balance_at_close,
                    incurred_amount,
                    payment_amount,
                    last_update_date
            FROM public.sched_d WHERE report_id = %s AND cmte_id = %s
            AND transaction_id = %s AND delete_ind is distinct from 'Y'
            """

            cursor.execute(
                """SELECT json_agg(t) FROM (""" + query_string + """) t""",
                (report_id, cmte_id, transaction_id),
            )

            schedD_list = cursor.fetchone()[0]

            if schedD_list is None:
                raise NoOPError(
                    "The transaction id: {} does not exist or is deleted".format(
                        transaction_id
                    )
                )
            merged_list = []
            for dictD in schedD_list:
                entity_id = dictD.get("entity_id")
                q_data = {"entity_id": entity_id, "cmte_id": cmte_id}
                entity_list = get_entities(q_data)
                dictEntity = entity_list[0]
                # merged_dict = {**dictD, **dictEntity}
                merged_list.append({**dictD, **dictEntity})
        return merged_list
    except Exception:
        raise
