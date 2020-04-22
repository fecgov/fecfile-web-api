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
    update_F3X
)
from fecfiler.sched_A.views import (
    get_next_transaction_id,
    find_form_type,
    find_aggregate_date,
)
from fecfiler.core.transaction_util import (
    transaction_exists,
    update_sched_d_parent,
    get_line_number_trans_type,
)
from fecfiler.sched_D.views import do_transaction
from fecfiler.core.report_helper import new_report_date

# TODO: add date validation: disbur and dissem should have at least one of them
# TODO: need to check and exclude memo transaction from aggregation

# Create your views here.
logger = logging.getLogger(__name__)

# TODO: may need to add the code for checking mandatory fields for aggregation
MANDATORY_FIELDS_SCHED_E = ["cmte_id", "report_id", "transaction_id"]
NEGATIVE_TRANSACTIONS = ["IE_VOID"]

# a list of child_parent IE transaction types
CHILD_PARENT_TRANSACTIONS = {
    "IE_CC_PAY_MEMO": "IE_CC_PAY",
    "IE_STAF_REIM_MEMO": "IE_STAF_REIM",
    "IE_PMT_TO_PROL_MEMO": "IE_PMT_TO_PROL_MEMO",
}


def check_transaction_id(transaction_id):
    if not (transaction_id[0:2] == "SE"):
        raise Exception(
            "The Transaction ID: {} is not in the specified format."
            + "Transaction IDs start with SE characters".format(transaction_id)
        )
    return transaction_id


def parent_transaction_exists(tran_id, sched_tp):
    """
    check if parent transaction exists
    """
    return transaction_exists(tran_id, sched_tp)


def validate_parent_transaction_exist(data):
    """
    validate parent transaction exsit if saving a child transaction
    """
    if data.get("transaction_type_identifier") in CHILD_PARENT_TRANSACTIONS:
        if not data.get("back_ref_transaction_id"):
            raise Exception("Error: parent transaction id missing.")
        elif not parent_transaction_exists(
            data.get("back_ref_transaction_id"), "sched_e"
        ):
            raise Exception("Error: parent transaction not found.")
        else:
            pass


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
        "cmte_id",
        "report_id",
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
        "expenditure_purpose_description",
        "category_code",
        "payee_cmte_id",
        "support_oppose_code",
        "so_cand_id",
        "so_cand_last_name",
        "so_cand_first_name",
        "so_cand_middle_name",
        "so_cand_prefix",
        "so_cand_suffix",
        "so_cand_office",
        "so_cand_district",
        "so_cand_state",
        "completing_entity_id",
        "date_signed",
        "memo_code",
        "memo_text_states",
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
        "aggregation_ind",
        "associatedbydissemination"
    ]
    try:
        datum = {k: v for k, v in data.items() if k in valid_fields}
        # so_ fields remapping to work with dynamic form
        # TODO: may need db fields renaming in the future
        so_cand_fields = [
            "so_cand_id",
            "so_cand_last_name",
            "so_cand_first_name",
            "so_cand_middle_name",
            "so_cand_prefix",
            "so_cand_suffix",
            "so_cand_office",
            "so_cand_district",
            "so_cand_state",
        ]
        for _f in so_cand_fields:
            if _f.replace("so_", "") in data:
                datum[_f] = data.get(_f.replace("so_", ""))
        # remap election code for frontend handshaking
        if "full_election_code" in data:
            datum["election_code"] = data.get("full_election_code")
        if "election_other_description" in data:
            datum["election_other_desc"] = data.get("election_other_description")

        # also add entity_id as an attribute. It is being remapped to payee_entity_id but fails in core since its looking for entity_id
        if "payee_entity_id" in data:
            datum["entity_id"] = data.get("payee_entity_id")
        datum["line_number"], datum["transaction_type"] = get_line_number_trans_type(
            data.get("transaction_type_identifier")
        )
        return datum
    except:
        raise Exception("invalid request data.")


def get_existing_expenditure_amount(cmte_id, transaction_id):
    """
    fetch existing expenditure amount in the db for current transaction
    """
    _sql = """
    select expenditure_amount
    from public.sched_e
    where cmte_id = %s
    and transaction_id = %s
    """
    _v = (cmte_id, transaction_id)
    try:
        with connection.cursor() as cursor:
            cursor.execute(_sql, _v)
            return cursor.fetchone()[0]
    except:
        raise

@update_F3X
@new_report_date
def put_schedE(data):
    """
    update sched_E item
    here we are assuming entity_id are always referencing something already in our DB
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

            # # need this update for FEC entity
            # if get_data["entity_id"].startswith("FEC"):
            #     get_data["cmte_id"] = "C00000000"
            old_entity = get_entities(get_data)[0]
            new_entity = put_entities(data)
            payee_rollback_flag = True
        else:
            logger.debug("saving new entity:{}".format(data))
            new_entity = post_entities(data)
            logger.debug("new entity created:{}".format(new_entity))
            payee_rollback_flag = False

        # continue to save transaction
        entity_id = new_entity.get("entity_id")
        # print('post_scheda {}'.format(entity_id))
        data["payee_entity_id"] = entity_id
        check_mandatory_fields_se(data)
        # check_transaction_id(data.get('transaction_id'))
        existing_expenditure = get_existing_expenditure_amount(
            data.get("cmte_id"), data.get("transaction_id")
        )
        try:
            put_sql_schedE(data)
            # update sched_d parent if IE debt payment
            if data.get("transaction_type_identifier") == "IE_B4_DISSE":
                if float(existing_expenditure) != float(data.get("expenditure_amount")):
                    update_sched_d_parent(
                        data.get("cmte_id"),
                        data.get("back_ref_transaction_id"),
                        data.get("expenditure_amount"),
                        existing_expenditure,
                    )
        except Exception as e:
            # remove entiteis if saving sched_e fails
            if payee_rollback_flag:
                entity_data = put_entities(old_entity)
            else:
                get_data = {"cmte_id": data.get("cmte_id"), "entity_id": entity_id}
                remove_entities(get_data)
            raise Exception(
                "The put_sql_schedE function is throwing an error: " + str(e)
            )
        update_aggregate_amt_se(data)
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
        report_id= %s,
        back_ref_transaction_id= %s,
        back_ref_sched_name= %s,
        payee_entity_id= %s,
        election_code= %s,
        election_other_desc= %s,
        dissemination_date= %s,
        expenditure_amount= %s,
        disbursement_date= %s,
        purpose= %s,
        category_code= %s,
        payee_cmte_id= %s,
        support_oppose_code= %s,
        so_cand_id= %s,
        so_cand_last_name= %s,
        so_cand_first_name= %s,
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
        aggregation_ind = %s,
        associatedbydissemination = %s,
        last_update_date= %s
    WHERE transaction_id = %s AND cmte_id = %s 
    AND delete_ind is distinct from 'Y';
    """
    _v = (
        data.get("transaction_type_identifier"),
        data.get("report_id"),
        data.get("back_ref_transaction_id"),
        data.get("back_ref_sched_name"),
        data.get("payee_entity_id"),
        data.get("election_code"),
        data.get("election_other_desc"),
        data.get("dissemination_date"),
        data.get("expenditure_amount"),
        data.get("disbursement_date"),
        data.get("expenditure_purpose_description"),
        data.get("category_code"),
        data.get("payee_cmte_id"),
        data.get("support_oppose_code"),
        data.get("so_cand_id"),
        data.get("so_cand_last_name"),
        data.get("so_cand_first_name"),
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
        data.get("aggregation_ind"),
        data.get("associatedbydissemination"),
        datetime.datetime.now(),
        data.get("transaction_id"),
        # data.get("report_id"),
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
    # print(transaction_id)
    # print(aggregate_amount)
    try:
        _sql = """
        UPDATE public.sched_e
        SET calendar_ytd_amount= %s
        WHERE transaction_id = %s AND cmte_id = %s 
        AND delete_ind is distinct from 'Y'
        """
        do_transaction(_sql, (aggregate_amount, transaction_id, cmte_id))
    except Exception as e:
        raise Exception(
            """error on update aggregate amount
                        for transaction:{}""".format(
                transaction_id
            )
        )


@api_view(["GET"])
def get_sched_e_ytd_amount(request):
    """
    get YTD amount based onelection code and office:
    if so_cand_office == 'P':
        only check against 'election code'
    if so_cand_office == 'S':
        need to check against election_code and so_cand_state
    if so_cand_office == 'H':
        need election_code, so_cand_state and so_cand_dsitrict
    """
    try:
        cmte_id = request.user.username
        cand_office = request.query_params.get("cand_office")
        if not cand_office:
            raise Exception("so_cand_office is required for this api.")
        election_code = request.query_params.get("election_code")
        if not election_code:
            raise Exception("election_code is required for this api.")
        if cand_office == "P":
            _sql = """
            SELECT calendar_ytd_amount, COALESCE(dissemination_date, disbursement_date) as transaction_dt 
            FROM public.sched_e
            WHERE cmte_id = %s
            AND so_cand_office = %s 
            AND election_code = %s 
            AND delete_ind is distinct from 'Y'
            ORDER BY transaction_dt DESC, create_date DESC; 
            """
            _v = (cmte_id, cand_office, election_code)
        elif cand_office == "S":
            cand_state = request.query_params.get("cand_state")
            if not cand_state:
                raise Exception("cand_state is required for cand_office S")
            _sql = """
            SELECT calendar_ytd_amount, COALESCE(dissemination_date, disbursement_date) as transaction_dt 
            FROM public.sched_e
            WHERE cmte_id = %s
            AND so_cand_office = %s 
            AND election_code = %s 
            AND so_cand_state = %s 
            AND delete_ind is distinct from 'Y'
            ORDER BY transaction_dt DESC, create_date DESC; 
            """
            _v = (cmte_id, cand_office, election_code, cand_state)
        elif cand_office == "H":
            cand_state = request.query_params.get("cand_state")
            cand_district = request.query_params.get("cand_district")
            if not cand_state:
                raise Exception("cand_state is required for cand_office H")
            if not cand_district:
                raise Exception("cand_district is required for cand_office H")
            _sql = """
            SELECT calendar_ytd_amount, COALESCE(dissemination_date, disbursement_date) as transaction_dt
            FROM public.sched_e
            WHERE cmte_id = %s
            AND so_cand_office = %s 
            AND election_code = %s 
            AND so_cand_state = %s 
            AND so_cand_district = %s 
            AND delete_ind is distinct from 'Y'
            ORDER BY transaction_dt DESC, create_date DESC; 
            """
            _v = (cmte_id, cand_office, election_code, cand_state, cand_district)
        else:
            raise Exception("invalid cand_office value.")
        with connection.cursor() as cursor:
            cursor.execute(_sql, _v)
            if not cursor.rowcount:
                logger.debug("no valid ytd value found.")
                ytd_amt = 0
            else:
                ytd_amt = cursor.fetchone()[0]
                logger.debug("ytd_amt fetched:{}".format(ytd_amt))
        return JsonResponse(
            {"ytd_amount": ytd_amt}, status=status.HTTP_200_OK, safe=False
        )
    except:
        raise


def get_transactions_election_and_office(start_date, end_date, data):
    """
    load all transactions by electtion code and office within the date range.
    - for president election: election_code + office
    - for senate electtion: election_code + office + state
    - for house: election_code + office + state + district

    when both dissemination_date and disbursement_date are available, 
    we take priority on dissemination_date 
    """
    _sql = ""
    _params = set([])
    cand_office = data.get("so_cand_office", data.get("cand_office"))
    if cand_office == "P":
        _sql = """
        SELECT  
                transaction_id, 
				expenditure_amount as transaction_amt,
				COALESCE(dissemination_date, disbursement_date) as transaction_dt,
                aggregation_ind
        FROM public.sched_e
        WHERE  
            cmte_id = %s
            AND COALESCE(dissemination_date, disbursement_date) >= %s
            AND COALESCE(dissemination_date, disbursement_date) <= %s
            AND election_code = %s
            AND delete_ind is distinct FROM 'Y'
            AND memo_code is null 
            ORDER BY transaction_dt ASC, create_date ASC;
        """
        _params = (data.get("cmte_id"), start_date, end_date, data.get("election_code"))
    elif cand_office == "S":
        _sql = """
        SELECT  
                transaction_id, 
				expenditure_amount as transaction_amt,
                COALESCE(dissemination_date, disbursement_date) as transaction_dt,
                aggregation_ind
        FROM public.sched_e
        WHERE  
            cmte_id = %s
            AND COALESCE(dissemination_date, disbursement_date) >= %s
            AND COALESCE(dissemination_date, disbursement_date) <= %s
            AND election_code = %s
            AND so_cand_state = %s
            AND delete_ind is distinct FROM 'Y' 
            AND memo_code is null
            ORDER BY transaction_dt ASC, create_date ASC; 
        """
        _params = (
            data.get("cmte_id"),
            start_date,
            end_date,
            data.get("election_code"),
            data.get("so_cand_state"),
        )
    elif cand_office == "H":
        _sql = """
        SELECT  
                transaction_id, 
				expenditure_amount as transaction_amt,
				COALESCE(dissemination_date, disbursement_date) as transaction_dt,
                aggregation_ind
        FROM public.sched_e
        WHERE  
            cmte_id = %s
            AND COALESCE(dissemination_date, disbursement_date) >= %s
            AND COALESCE(dissemination_date, disbursement_date) <= %s
            AND election_code = %s
            AND so_cand_state = %s
            AND so_cand_district = %s
            AND delete_ind is distinct FROM 'Y' 
            AND memo_code is null
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
        # dissemination_date, disbursement_date = data.get('dissemination_date'), data.get('disbursement_date')
        # curr_tran_date = dissemination_date if dissemination_date else disbursement_date 
        # curr_tran_date =  datetime.datetime.strptime(
        #                     curr_tran_date, "%Y-%m-%d"
        #                 ).date()
        for transaction in transaction_list:
            if transaction[3] != 'N':
                aggregate_amount += transaction[1]
            logger.debug(
                "update aggregate amount for transaction:{}".format(transaction[0])
            )
            logger.debug("current aggregate amount:{}".format(aggregate_amount))
            # if curr_tran_date <= transaction[2]:
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


def post_completing_entities(data):
    """
    a warpper function for saving completing entity
    """
    comp_data = {
        k.replace("completing_", ""): v
        for k, v in data.items()
        if k.startswith("completing_")
    }
    comp_data["cmte_id"] = data.get("cmte_id")
    if "prefix" in comp_data:
        comp_data["preffix"] = comp_data.get("prefix")
    comp_data["entity_type"] = "IND"
    logger.debug("post_completing_entity with data:{}".format(comp_data))
    return post_entities(comp_data)


def put_completing_entities(data):
    """
    helper function to filter  completing entity data and save it
    """
    comp_data = {
        k.replace("completing_", ""): v
        for k, v in data.items()
        if k.startswith("completing_")
    }
    comp_data["cmte_id"] = data.get("cmte_id")
    if "prefix" in comp_data:
        comp_data["preffix"] = comp_data.get("prefix")
    comp_data["entity_type"] = "IND"
    logger.debug("put_auth_entity with data:{}".format(comp_data))
    return put_entities(comp_data)

@update_F3X
@new_report_date
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
        if "entity_id" in data:
            logger.debug("update payee entity with data:{}".format(data))
            get_data = {
                "cmte_id": data.get("cmte_id"),
                "entity_id": data.get("entity_id"),
            }

            # need this update for FEC entity
            if get_data["entity_id"].startswith("FEC"):
                get_data["cmte_id"] = "C00000000"
            old_entity = get_entities(get_data)[0]
            new_entity = put_entities(data)
            payee_rollback_flag = True
        else:
            logger.debug("saving new entity:{}".format(data))
            new_entity = post_entities(data)
            logger.debug("new entity created:{}".format(new_entity))
            payee_rollback_flag = False

        # continue to save transaction
        payee_entity_id = new_entity.get("entity_id")
        # print('post_scheda {}'.format(entity_id))
        data["payee_entity_id"] = payee_entity_id

        if "completing_entity_id" in data:
            logger.debug("update completing entity with data:{}".format(data))
            get_data = {
                "cmte_id": data.get("cmte_id"),
                "entity_id": data.get("completing_entity_id"),
            }

            # need this update for FEC entity
            if get_data["entity_id"].startswith("FEC"):
                get_data["cmte_id"] = "C00000000"
            old_completing_entity = get_entities(get_data)[0]
            new_completing_entity = put_completing_entities(data)
            completing_rollback_flag = True
        else:
            logger.debug("saving new completing entity:{}".format(data))
            new_completing_entity = post_completing_entities(data)
            logger.debug("new entity created:{}".format(new_entity))
            completing_rollback_flag = False
        data["completing_entity_id"] = new_completing_entity.get("entity_id")

        data["transaction_id"] = get_next_transaction_id("SE")
        # print(data)

        validate_se_data(data)
        validate_negative_transaction(data)
        validate_parent_transaction_exist(data)
        data = schedE_sql_dict(data)
        # TODO: add code for saving completing_entity

        try:
            logger.debug("saving new sched_e item with data:{}".format(data))
            post_sql_schedE(data)

            # update sched_d parent if IE debt payment
            if data.get("transaction_type_identifier") == "IE_B4_DISSE":
                update_sched_d_parent(
                    data.get("cmte_id"),
                    data.get("back_ref_transaction_id"),
                    data.get("expenditure_amount"),
                )
        except Exception as e:
            # remove entiteis if saving sched_e fails
            if payee_rollback_flag:
                entity_data = put_entities(old_entity)
            else:

                get_data = {
                    "cmte_id": data.get("cmte_id"),
                    "entity_id": payee_entity_id,
                }
                logger.debug(
                    "exception happened, removing payee entity:{}".format(
                        payee_entity_id
                    )
                )
                remove_entities(get_data)

            if completing_rollback_flag:
                entity_data = put_entities(old_completing_entity)
            else:
                get_data = {
                    "cmte_id": data.get("cmte_id"),
                    "entity_id": data.get("completing_entity_id"),
                }
                logger.debug(
                    "removing completing entity:{}".format(
                        data.get("completing_entity_id")
                    )
                )
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
            so_cand_first_name,
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
            aggregation_ind,
            associatedbydissemination,
            create_date
            )
        VALUES ({})
        """.format(
            ",".join(["%s"] * 34)
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
            data.get("expenditure_purpose_description"),
            data.get("category_code"),
            data.get("payee_cmte_id"),
            data.get("support_oppose_code"),
            data.get("so_cand_id"),
            data.get("so_cand_last_name"),
            data.get("so_cand_first_name"),
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
            data.get("aggregation_ind"),
            data.get("associatedbydissemination"),
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
        if forms_obj:
            for SE in forms_obj:
                SE["election_other_description"] = SE.get("election_other_desc")
                if SE["associatedbydissemination"]:
                    SE["associated_report_id"] = SE["report_id"]
                child_SE = get_list_schedE(
                    SE["report_id"], SE["cmte_id"], SE["transaction_id"], True
                )
                if child_SE:
                    SE["child"] = child_SE
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
            so_cand_first_name,
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


def mapFieldsForUI(data):
    """
    mapping response fields to frontend fields
    """
    # so_ fields remapping to work with frontend
    # TODO: may need db fields renaming in the future
    cand_fields = [
        "so_cand_id",
        "so_cand_last_name",
        "so_cand_first_name",
        "so_cand_middle_name",
        "so_cand_prefix",
        "so_cand_suffix",
        "so_cand_office",
    ]
    for _f in cand_fields:
        if _f in data:
            data[_f.replace("so_", "")] = data.pop(_f)
    data["cand_office_state"] = data["so_cand_state"]
    data.pop("so_cand_state")
    data["cand_office_district"] = data["so_cand_district"]
    data.pop("so_cand_district")
    data["full_election_code"] = data["election_code"]
    data["cand_election_year"] = data["election_code"][-4:]
    data["election_code"] = data["election_code"][0:-4]
    data["expenditure_aggregate"] = data["calendar_ytd_amount"]
    data.pop("calendar_ytd_amount")
    data["beneficiary_cand_id"] = data["cand_id"]
    data.pop("cand_id")
    data["expenditure_purpose_description"] = data["purpose"]
    data.pop("purpose")
    # data['aggregate'] = data['expenditure_aggregate'] #this should be mapped more cleanly. Right now sending a duplicate of expenditure_aggregate

    return data


def get_list_schedE(report_id, cmte_id, transaction_id, is_back_ref=False):
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
            so_cand_first_name,
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
            aggregation_ind,
            associatedbydissemination,
            create_date, 
            last_update_date
            FROM public.sched_e
            WHERE 
            
            cmte_id = %s 
            AND delete_ind is distinct from 'Y'
            """
            if is_back_ref:
                _sql = _sql + """ AND report_id = %s AND  back_ref_transaction_id = %s) t"""
                cursor.execute(_sql, (cmte_id, report_id, transaction_id))
            else:
                _sql = _sql + """ AND transaction_id = %s) t"""
                cursor.execute(_sql, (cmte_id, transaction_id))
            schedE_list = cursor.fetchone()[0]
            if schedE_list is None and not is_back_ref:
                raise NoOPError(
                    "No sched_e transaction found for transaction_id {}".format(
                        transaction_id
                    )
                )
            merged_list = []
            if schedE_list:
                for dictE in schedE_list:
                    dictE["api_call"] = "/se/schedE"
                    # get payee, completing entities and merge
                    entity_ids = ["payee_entity_id", "completing_entity_id"]
                    for _id in entity_ids:
                        entity_id = dictE.get(_id)
                        data = {"entity_id": entity_id, "cmte_id": dictE["cmte_id"]}
                        entity_data = get_entities(data)[0]
                        if _id == "completing_entity_id":
                            prefix = _id.split("_")[0]
                            entity_data = {
                                (prefix + "_" + k): v for k, v in entity_data.items()
                            }
                        dictE.update(entity_data)
                    dictE = mapFieldsForUI(dictE)
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


def update_se_aggregation_status(transaction_id, status):
    """
    helpder function to update sa aggregation_ind
    """
    _sql = """
    update public.sched_e
    set aggregation_ind = %s
    where transaction_id = %s
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(_sql, [status, transaction_id])
            if cursor.rowcount == 0:
                raise Exception(
                    "The Transaction ID: {} does not exist in se table".format(
                        transaction_id
                    )
                )
    except:
        raise


@api_view(["PUT"])
def force_aggregate_se(request):
    """
    api to force a transaction to be aggregated:
    1. set aggregate_ind = 'Y'
    2. re-do entity-based aggregation on se
    """
    try:
        cmte_id = request.user.username
        report_id = request.data.get("report_id")
        transaction_id = request.data.get("transaction_id")
        if not transaction_id:
            raise Exception("transaction id is required for this api call.")
        update_se_aggregation_status(transaction_id, "Y")
        tran_data = get_list_schedE(report_id, cmte_id, transaction_id)[0]
        update_aggregate_amt_se(tran_data)
        return JsonResponse(
                {"status": "success"}, status=status.HTTP_200_OK
            )
    except Exception as e:
        return Response(
            "The force_aggregate_se API is throwing an error: " + str(e),
            status=status.HTTP_400_BAD_REQUEST,
        )


@api_view(["PUT"])
def force_unaggregate_se(request):
    """
    api to force a transaction to be un-aggregated:
    1. set aggregate_ind = 'N'
    2. re-do entity-based aggregation on se
    """
    try:
        cmte_id = request.user.username
        report_id = request.data.get("report_id")
        transaction_id = request.data.get("transaction_id")
        if not transaction_id:
            raise Exception("transaction id is required for this api call.")
        update_se_aggregation_status(transaction_id, "N")
        tran_data = get_list_schedE(report_id, cmte_id, transaction_id)[0]
        update_aggregate_amt_se(tran_data)
        return JsonResponse(
                {"status": "success"}, status=status.HTTP_200_OK
            )
    except Exception as e:
        return Response(
            "The force_aggregate_se API is throwing an error: " + str(e),
            status=status.HTTP_400_BAD_REQUEST,
        )


@api_view(["POST", "GET", "DELETE", "PUT"])
def schedE(request):
    """
    this is the sched_e api
    """
    if request.method == "POST":
        try:
            cmte_id = request.user.username
            associatedbydissemination = False
            if not ("report_id" in request.data):
                raise Exception("Missing Input: Report_id is mandatory")
            # handling null,none value of report_id
            if not (check_null_value(request.data.get("report_id"))):
                report_id = "0"
            else:
                report_id = check_report_id(request.data.get("report_id"))
            # end of handling
            #also check if an 'override' report_id present, and if so, use that instead. 
            if(request.data.get("associated_report_id") and check_null_value(request.data.get("associated_report_id"))):
                report_id = request.data.get("associated_report_id")
                associatedbydissemination = True
            # datum = schedE_sql_dict(request.data)
            datum = request.data.copy()
            datum["report_id"] = report_id
            datum["cmte_id"] = cmte_id
            datum["associatedbydissemination"] = associatedbydissemination
            if datum["transaction_type_identifier"] == "IE_MULTI":
                if "memo_text" in datum:
                    datum["memo_text"] = (
                        datum["memo_text_states"] + " - " + datum["memo_text"]
                    )
                else:
                    datum["memo_text"] = datum["memo_text_states"] + " - "
            if "beneficiary_cand_id" in request.data:
                datum["so_cand_id"] = request.data["beneficiary_cand_id"]
            if "cand_office_state" in request.data:
                datum["so_cand_state"] = request.data["cand_office_state"]
            if "cand_office_district" in request.data:
                datum["so_cand_district"] = request.data["cand_office_district"]
            if "transaction_id" in request.data and check_null_value(
                request.data.get("transaction_id")
            ):
                datum["transaction_id"] = check_transaction_id(
                    request.data.get("transaction_id")
                )
                data = put_schedE(datum)
            else:
                # print(datum)
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
            associatedbydissemination = False

            if datum["transaction_type_identifier"] == "IE_MULTI":
                if "memo_text" in datum:
                    datum["memo_text"] = (
                        datum["memo_text_states"] + " - " + datum["memo_text"]
                    )
                else:
                    datum["memo_text"] = datum["memo_text_states"] + " - "
            if "beneficiary_cand_id" in request.data:
                datum["so_cand_id"] = request.data["beneficiary_cand_id"]
            if "cand_office_state" in request.data:
                datum["so_cand_state"] = request.data["cand_office_state"]
            if "cand_office_district" in request.data:
                datum["so_cand_district"] = request.data["cand_office_district"]
            if "cand_office" in request.data:
                datum["so_cand_office"] = request.data["cand_office"]

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
            #also check if an 'override' report_id present, and if so, use that instead. 
            if(request.data.get("associated_report_id") and check_null_value(request.data.get("associated_report_id"))):
                report_id = request.data.get("associated_report_id")
                associatedbydissemination = True
            datum["report_id"] = report_id
            datum["cmte_id"] = request.user.username
            datum["associatedbydissemination"] = associatedbydissemination

            data = put_schedE(datum)
            output = get_schedE(data)
            return JsonResponse(output[0], status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.debug(e)
            return Response(
                "The schedE API - PUT is throwing an error: " + str(e),
                status=status.HTTP_400_BAD_REQUEST,
            )

    else:
        raise NotImplementedError
