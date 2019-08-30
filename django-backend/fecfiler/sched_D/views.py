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

# from fecfiler.sched_B.views import (delete_parent_child_link_sql_schedB,
#                                     delete_schedB, get_list_child_schedB,
#                                     get_schedB, post_schedB, put_schedB,
#                                     schedB_sql_dict)

# Create your views here.
logger = logging.getLogger(__name__)

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
            datum = schedD_sql_dict(request.data)
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
                data = put_schedD(datum)
            else:
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
            if "report_id" in request.data:
                data["report_id"] = check_report_id(request.data.get("report_id"))
            else:
                raise Exception("Missing Input: report_id is mandatory")
            if "transaction_id" in request.data and check_null_value(
                request.data.get("transaction_id")
            ):
                data["transaction_id"] = check_transaction_id(
                    request.data.get("transaction_id")
                )
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
            if "report_id" in request.data:
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
            # output = get_schedA(data)
            return JsonResponse(data, status=status.HTTP_201_CREATED)
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
        "creditor_entity_id",
        "purpose",
        "beginning_balance",
        "incurred_amount",
        "payment_amount",
        "balance_at_close",
        "line_number",
    ]
    try:
        return {k: v for k, v in data.items() if k in valid_fields}
    except:
        raise Exception("invalid request data.")


def put_schedD(datum):
    """update sched_d item
    here we are assuming creditor_entoty_id are always referencing something already in our DB
    """
    try:
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
            # if flag:
            #     entity_data = put_entities(prev_entity_list[0])
            # else:
            #     get_data = {
            #         'cmte_id': datum.get('cmte_id'),
            #         'entity_id': entity_id
            #     }
            #     remove_entities(get_data)
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
                "The following mandatory fields are required in order to save data to schedA table: {}".format(
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
            # if 'creditor_entity_id' in datum:
            #     entity_data = put_entities(prev_entity_list[0])
            # else:
            #     get_data = {
            #         'cmte_id': datum.get('cmte_id'),
            #         'entity_id': creditor_entity_id
            #     }
            #     remove_entities(get_data)
            raise Exception(
                "The post_sql_schedD function is throwing an error: " + str(e)
            )
        # update line number based on aggregate amount info
        # update_linenumber_aggamt_transactions_SA(datum.get('contribution_date'), datum.get(
        #     'transaction_type'), entity_id, datum.get('cmte_id'), datum.get('report_id'))
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
                                    creditor_entity_id,
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
            data.get("transaction_type_identifier", ""),
            data.get("transaction_id"),
            data.get("creditor_entity_id", ""),
            data.get("purpose", ""),
            data.get("beginning_balance", None),
            data.get("incurred_amount", None),
            data.get("payment_amount", None),
            data.get("balance_at_close", None),
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
                creditor_entity_id = %s,
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
        data.get("transaction_type_identifier", ""),
        data.get("line_number"),
        data.get("creditor_entity_id", ""),
        data.get("purpose", ""),
        data.get("beginning_balance", ""),
        data.get("balance_at_close", ""),
        data.get("incurred_amount", ""),
        data.get("payment_amount", ""),
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


def get_schedD(data):
    try:
        cmte_id = data.get("cmte_id")
        report_id = data.get("report_id")
        if "transaction_id" in data:
            transaction_id = check_transaction_id(data.get("transaction_id"))
            forms_obj = get_list_schedD(report_id, cmte_id, transaction_id)
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
                    creditor_entity_id, 
                    beginning_balance, 
                    balance_at_close, 
                    incurred_amount, 
                    payment_amount, 
                    last_update_date
            FROM public.sched_d 
            WHERE report_id = %s 
            AND cmte_id = %s 
            AND delete_ind is distinct from 'Y';
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
                # entity_id = dictA.get('entity_id')
                # data = {
                #     'entity_id': entity_id,
                #     'cmte_id': cmte_id
                # }
                # entity_list = get_entities(data)
                # dictEntity = entity_list[0]
                # merged_dict = {**dictA, **dictEntity}
                merged_list.append(dictD)
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
                    creditor_entity_id,
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
                merged_list.append(dictD)
        return merged_list
    except Exception:
        raise
