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
    get_sched_a_transactions,
    get_sched_b_transactions,
    get_sched_e_child_transactions,
    get_sched_f_child_transactions,
    get_sched_h4_child_transactions,
    get_sched_h6_child_transactions,
    get_transaction_type_descriptions,
    # do_carryover_sc_payments,
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
    update_F3X
)
from fecfiler.sched_A.views import get_next_transaction_id
from fecfiler.core.report_helper import new_report_date

# from fecfiler.sched_B.views import (delete_parent_child_link_sql_schedB,
#                                     delete_schedB, get_list_child_schedB,
#                                     get_schedB, post_schedB, put_schedB,
#                                     schedB_sql_dict)

# Create your views here.
logger = logging.getLogger(__name__)

API_CALL_SA = {"api_call": "/sa/schedA", "sched_type": "sched_a"}
API_CALL_SB = {"api_call": "/sb/schedB", "sched_type": "sched_b"}
API_CALL_SF = {"api_call": "/sf/schedF", "sched_type": "sched_f"}
API_CALL_SE = {"api_call": "/se/schedE", "sched_type": "sched_e"}
API_CALL_SH4 = {"api_call": "/sh4/schedH4", "sched_type": "sched_h4"}
API_CALL_SH6 = {"api_call": "/sh6/schedH6", "sched_type": "sched_h6"}

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
            if 'transaction_type_identifier' in request.query_params:
                data['transaction_type_identifier'] = request.query_params.get(
                    'transaction_type_identifier')
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
            data.get("cmte_id"), data.get(
                "report_id"), data.get("transaction_id")
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
        "purpose",
        "beginning_balance",
        "incurred_amount",
        "payment_amount",
        "balance_at_close",
        "line_number",
        "back_ref_transaction_id",
        "back_ref_sched_name",
        # entity_data
        "entity_id",
        "entity_type",
        "entity_name",
        "first_name",
        "last_name",
        "middle_name",
        "prefix",
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
        if valid_transaction_amounts(data):
            return valid_data
        else:
            raise Exception("transaction amounts does not add up together.")
    except:
        raise Exception("invalid request data.")


def valid_transaction_amounts(data):
    """
    make sure transaction amounts add up
    beginning_balance + incurred_amount - payment == balance_at_close
    """
    beginning_balance = data.get("beginning_balance")
    if not beginning_balance:
        beginning_balance = 0
    balance_at_close = data.get("balance_at_close")
    if not balance_at_close:
        balance_at_close = 0
    incurred_amount = data.get("incurred_amount")
    if not incurred_amount:
        incurred_amount = 0
    payment_amount = data.get("payment_amount")
    if not payment_amount:
        payment_amount = 0
    return (
        float(beginning_balance) +
        float(incurred_amount) - float(payment_amount)
    ) == float(balance_at_close)

@update_F3X
@new_report_date
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
        cmte_id = datum.get("cmte_id")
        report_id = datum.get("report_id")
        current_close_balance = float(datum.get("balance_at_close"))
        existing_close_balance = float(
            get_existing_close_balance(cmte_id, report_id, transaction_id)
        )
        try:
            put_sql_schedD(datum)
            # do downstream proprgation if necessary
            if not existing_close_balance == current_close_balance:
                do_downstream_propagation(
                    transaction_id, current_close_balance)
        except Exception as e:
            if entity_flag:
                entity_data = put_entities(prev_entity_list[0])
            else:
                get_data = {"cmte_id": datum.get(
                    "cmte_id"), "entity_id": entity_id}
                remove_entities(get_data)
            raise Exception(
                "The put_sql_schedD function is throwing an error: " + str(e)
            )
        return datum
    except:
        raise


def get_existing_close_balance(cmte_id, report_id, transaction_id):
    """
    fetch existing close balance in the db for current transaction
    """
    _sql = """
    select balance_at_close
    from public.sched_d
    where cmte_id = %s
    and report_id = %s
    and transaction_id = %s
    """
    _v = (cmte_id, report_id, transaction_id)
    try:
        with connection.cursor() as cursor:
            cursor.execute(_sql, _v)
            return cursor.fetchone()[0]
    except:
        raise


def has_downstream_child(transaction_id):
    """
    check if current sched_d transaction has other carry over child or not
    """
    _sql = """
    select * from public.sched_d 
    where back_ref_transaction_id = %s
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(_sql, (transaction_id))
            return cursor.rowcount != 0
    except:
        raise


def update_child(transaction_id, new_beginning_balance, new_close_balance):
    """
    update child transaction beginning balance and close balance
    """
    _sql = """
            UPDATE public.sched_d
            SET beginning_balance = %s,
                balance_at_close = %s,
                last_update_date = %s
            WHERE transaction_id = %s 
            AND delete_ind is distinct from 'Y';
        """
    _v = (new_close_balance, new_close_balance,
          datetime.datetime.now(), transaction_id)
    logger.debug("update child sched_d with values: {}".format(_v))
    do_transaction(_sql, _v)


def do_downstream_propagation(transaction_id, new_balance):
    """

    1. query child amount fileds
    2. re-calcualte close_balance
    3. save new value: beginning balance and close balance
    4. return child transaction id and new close balance for propagation

    """
    logger.debug("doing downstream propagation updates...")
    logger.debug("current transaction id:{}".format(transaction_id))
    logger.debug("current balance:{}".format(new_balance))

    _sql = """
        SELECT transaction_id, incurred_amount, payment_amount
        FROM public.sched_d 
        WHERE back_ref_transaction_id = '{}'
            AND delete_ind is distinct from 'Y'
    """.format(
        transaction_id
    )
    try:
        new_beginning_balance = new_balance
        with connection.cursor() as cursor:
            cursor.execute(_sql)

            # no child found anymore, return; propagation update done
            if cursor.rowcount == 0:
                logger.debug("no child found any more.")
                return

            child_tran = cursor.fetchone()

            child_id = child_tran[0]
            logger.debug("child id:{}".format(child_id))
            incurred_amt = child_tran[1]
            payment_amt = child_tran[2]
            new_close_balance = (
                float(new_beginning_balance) +
                float(incurred_amt) - float(payment_amt)
            )
            logger.debug("new close balance:{}".format(new_close_balance))
            update_child(child_id, new_beginning_balance, new_close_balance)
            # recrusive update
            do_downstream_propagation(child_id, new_close_balance)
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

@update_F3X
@new_report_date
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
                get_data = {"cmte_id": datum.get(
                    "cmte_id"), "entity_id": entity_id}
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
                                    back_ref_transaction_id,
                                    back_ref_sched_name,
                                    create_date)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);
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
            data.get("back_ref_transaction_id"),
            data.get("back_ref_sched_name"),
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
                back_ref_transaction_id = %s,
                back_ref_sched_name = %s,
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
        data.get("back_ref_transaction_id"),
        data.get("back_ref_sched_name"),
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
                raise Exception(
                    "The sql transaction: {} failed...".format(sql))
    except Exception:
        raise


def get_child_transactions(report_id, cmte_id, transaction_id):
    """
    adding all the pissible child transactions:
    sched_b, ached_e, sched_f, sched_h4, sched_h6
    TODO: need to add sched_e child data later on
    """
    sched_a_list = get_sched_a_transactions(
        report_id, cmte_id, back_ref_transaction_id=transaction_id
    )
    sched_b_list = get_sched_b_transactions(
        report_id, cmte_id, back_ref_transaction_id=transaction_id
    )
    # TODO: will add all other transactions later on
    sched_e_list = get_sched_e_child_transactions(
        report_id, cmte_id, transaction_id)
    sched_f_list = get_sched_f_child_transactions(
        report_id, cmte_id, transaction_id)
    sched_h4_list = get_sched_h4_child_transactions(
        report_id, cmte_id, transaction_id)
    sched_h6_list = get_sched_h6_child_transactions(
        report_id, cmte_id, transaction_id)
    return sched_a_list + sched_b_list + sched_e_list + sched_f_list + sched_h4_list + sched_h6_list

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
        tran_desc_dic = get_transaction_type_descriptions()
        if "transaction_id" in data:
            transaction_id = check_transaction_id(data.get("transaction_id"))
            forms_obj = get_list_schedD(report_id, cmte_id, transaction_id)

        else:
            transaction_type_identifier = data.get(
                'transaction_type_identifier', '')
            # when laod sched_d in bulk, need to do a carry-over when new report_id
            # passed in: duplicate all non-zero sched_d items with updated report_id
            # new transaction_id, close

            # if is_new_report(report_id, cmte_id):
            logger.debug(
                "checking and doing carryover on sched_d: cmte-id {}, report_id {}".format(
                    cmte_id, report_id
                )
            )
            do_carryover(report_id, cmte_id)
            forms_obj = get_list_all_schedD(
                report_id, cmte_id, transaction_type_identifier)
        logger.debug("total schedD items loaded:{}".format(len(forms_obj)))
        if forms_obj:
            for f_obj in forms_obj:

                tran_id = f_obj.get("transaction_type_identifier")
                f_obj.update(
                    {"transaction_type_description": tran_desc_dic.get(
                        tran_id, "")}
                )
                transaction_id = f_obj.get("transaction_id")
                child_objs = get_child_transactions(
                    report_id, cmte_id, transaction_id)
                logger.debug("total childs:{}".format(len(child_objs)))
                if child_objs:
                    logger.debug
                    for (
                        obj
                    ) in child_objs:  # this api_call code need to refactored later on
                        tran_id = obj.get("transaction_type_identifier")
                        obj.update(
                            {
                                "transaction_type_description": tran_desc_dic.get(
                                    tran_id, ""
                                )
                            }
                        )
                        obj.update({"back_ref_api_call": "/sd/schedD"})
                        if obj["transaction_id"].startswith("SA"):
                            obj.update(API_CALL_SA)
                            # obj['transaction_amount'] = obj.pop('contribution_amount')
                            # obj['transaction_date'] = obj.pop('contribution_date')
                        if obj["transaction_id"].startswith("SB"):
                            obj.update(API_CALL_SB)
                        if obj["transaction_id"].startswith("SE"):
                            obj.update(API_CALL_SE)
                        if obj["transaction_id"].startswith("SF"):
                            obj.update(API_CALL_SF)
                        if "levin_share" in obj:
                            obj['expenditure_amount'] = obj.get('total_fed_levin_amount', 0.0)
                            obj.update(API_CALL_SH6)
                        if "non_fed_share_amount" in obj:
                            obj['expenditure_amount'] = obj.get('total_amount', 0.0)
                            obj.update(API_CALL_SH4)
                        f_obj["child"] = child_objs
        return forms_obj
    except:
        raise


def is_new_report(report_id, cmte_id):
    """
    check if a report_id is new or not
    a report_id is new if:
    1.  not exist in sched_d table 
    2. and the cvg_date is newer than the most recent one

    TODO: may need to reconsider this
    NOTE: deprecated: this is not true for amendment
    """
    # _sql = """
    # select * from public.sched_d
    # where report_id = %s and cmte_id = %s
    # """
    _sql = """
        SELECT 1 AS seq, 
            cvg_start_date 
        FROM   PUBLIC.reports 
        WHERE  report_id = %s
        UNION 
        SELECT 2 AS seq, 
            Max(cvg_end_date) 
        FROM   PUBLIC.reports r 
            JOIN PUBLIC.sched_d sd 
                ON r.report_id = sd.report_id 
                    AND r.cmte_id = sd.cmte_id 
                    AND r.cmte_id = %s
        ORDER  BY seq 
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(_sql, (report_id, cmte_id))
            results = cursor.fetchall()
            new_date = results[0][1]
            old_date = results[1][1]
            if new_date and old_date and new_date > old_date:
                return True
            return False
    except:
        raise


def do_carryover(report_id, cmte_id):
    """
    this is the function to handle debt carryover form one report to next report:
    1. load all non-zero close_balance sched_d and make sure:
    - debt incurred date < report coverge start
    - only load non-parent items

    2. update all records with new transaction_id, new report_id
    3. copy close_balance to starting_balance, leave all other amount 0
    4. insert sched_c into db
    """
    _sql = """
    insert into public.sched_d(
					cmte_id, 
                    report_id, 
                    line_num,
                    transaction_type_identifier, 
                    transaction_id, 
                    entity_id, 
                    beginning_balance, 
                    balance_at_close, 
                    incurred_amount, 
                    payment_amount, 
					purpose,
                    back_ref_transaction_id,
                    create_date
					)
					SELECT 
					d.cmte_id, 
                    %s, 
                    d.line_num,
                    d.transaction_type_identifier, 
                    get_next_transaction_id('SD'), 
                    d.entity_id, 
                    d.balance_at_close, 
                    d.balance_at_close, 
                    0, 
                    0, 
					d.purpose,
                    d.transaction_id,
                    now()
            FROM public.sched_d d, public.reports r
            WHERE 
            d.cmte_id = %s
            AND d.balance_at_close > 0 
            AND d.report_id != %s
            AND d.report_id = r.report_id
            AND r.cvg_start_date < (
                        SELECT r.cvg_start_date
                        FROM   public.reports r
                        WHERE  r.report_id = %s
                    )
            AND d.transaction_id NOT In (
                select distinct d1.back_ref_transaction_id from public.sched_d d1
                where d1.cmte_id = %s
                and d1.back_ref_transaction_id is not null
                and d1.delete_ind is distinct from 'Y'
            )
            AND d.delete_ind is distinct from 'Y' ;
    """
    # query_back_sql = """
    # select d.back_ref_transaction_id
    # """
    try:
        with connection.cursor() as cursor:
            cursor.execute(_sql, (report_id, cmte_id,
                                  report_id, report_id, cmte_id))
            if cursor.rowcount == 0:
                logger.debug("No carryover happens.")
            else:
                logger.debug(
                    "debt carryover done with report_id {}".format(report_id))
                logger.debug(
                    "total carryover debts:{}".format(cursor.rowcount))
                # do_carryover_sc_payments(cmte_id, report_id, cursor.rowcount)
                logger.debug("carryover done.")
    except:
        raise


def get_list_all_schedD(report_id, cmte_id, transaction_type_identifier):
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
                    back_ref_transaction_id,
                    back_ref_sched_name,
                    last_update_date
            FROM public.sched_d 
            WHERE report_id = %s 
            AND cmte_id = %s 
            AND delete_ind is distinct from 'Y'
            """
            type_filter = 'AND transaction_type_identifier = %s'
            if transaction_type_identifier:
                cursor.execute(
                    """SELECT json_agg(t) FROM (""" +
                    query_string + type_filter + """) t""",
                    (report_id, cmte_id, transaction_type_identifier),
                )
            else:
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
            # query_string = """
            # SELECT cmte_id,
            #         report_id,
            #         line_num,
            #         transaction_type_identifier,
            #         transaction_id,
            #         entity_id,
            #         beginning_balance,
            #         balance_at_close,
            #         incurred_amount,
            #         payment_amount,
            #         last_update_date
            # FROM public.sched_d WHERE report_id = %s AND cmte_id = %s
            # AND transaction_id = %s AND delete_ind is distinct from 'Y'
            # """

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
                    back_ref_transaction_id,
                    back_ref_sched_name,
                    balance_at_close,
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
