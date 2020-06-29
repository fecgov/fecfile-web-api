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
from django.core.paginator import Paginator
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from fecfiler.authentication.authorization import is_read_only_or_filer_reports
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
    get_comittee_id,
    update_F3X

)
from fecfiler.core.transaction_util import (
    get_line_number_trans_type,
    transaction_exists,
    update_sched_d_parent,
    cmte_type,
    get_sched_h4_child_transactions,
    get_sched_h6_child_transactions,
)

from fecfiler.sched_A.views import get_next_transaction_id
from fecfiler.sched_D.views import do_transaction
from fecfiler.core.report_helper import new_report_date


# Create your views here.
logger = logging.getLogger(__name__)

MANDATORY_FIELDS_SCHED_H1 = [
    "cmte_id",
    "report_id",
    "transaction_id",
    "transaction_type_identifier",
    "federal_percent",
    "non_federal_percent",
]
MANDATORY_FIELDS_SCHED_H2 = [
    "cmte_id",
    "report_id",
    "transaction_id",
    "transaction_type_identifier",
    "federal_percent",
    "non_federal_percent",
]
MANDATORY_FIELDS_SCHED_H3 = [
    "cmte_id",
    "report_id",
    "transaction_id",
    "transaction_type_identifier",
]
MANDATORY_FIELDS_SCHED_H4 = [
    "cmte_id",
    "report_id",
    "transaction_id",
    "transaction_type_identifier",
]
MANDATORY_FIELDS_SCHED_H5 = ["cmte_id", "report_id", "transaction_id"]
MANDATORY_FIELDS_SCHED_H6 = ["cmte_id", "report_id", "transaction_id"]


def check_transaction_id(transaction_id):
    if not (transaction_id[0:2] == "SH"):
        raise Exception(
            "The Transaction ID: {} is not in the specified format."
            + "Transaction IDs start with SH characters".format(transaction_id)
        )
    return transaction_id


"""
SCHED_H1:

Method of Allocation for:
- Allocated Administrative and Generic Voter Drive Costs
- Allocated Exempt Party Activity Costs (Party Committees Only)
- Allocated Public Communications that Refer to any Political Party (but not
a candidate) (Separate Segregated Funds and Nonconnected Committees
Only) 
"""


def schedH1_sql_dict(data):
    """
    filter out valid fileds for sched_H1

    """
    valid_h1_fields = [
        "line_number",
        "transaction_type_identifier",
        "transaction_type",
        "presidential_only",
        "presidential_and_senate",
        "senate_only",
        "non_pres_and_non_senate",
        "federal_percent",
        "non_federal_percent",
        "election_year",
        "administrative",
        "generic_voter_drive",
        "public_communications",
    ]
    try:
        # return {k: v for k, v in data.items() if k in valid_h1_fields}
        datum = {k: v for k, v in data.items() if k in valid_h1_fields}
        datum["line_number"], datum["transaction_type"] = get_line_number_trans_type(
            data.get("transaction_type_identifier")
        )
        # print(datum)
        return datum
    except:
        raise Exception("invalid h1 request data.")


def check_mandatory_fields_SH1(data):
    """
    check madatroy frields for sh1
    """
    try:
        errors = []
        for field in MANDATORY_FIELDS_SCHED_H1:
            if not (field in data and check_null_value(data.get(field))):
                errors.append(field)
        if errors:
            raise Exception(
                "The following mandatory fields are required in order to save data to schedH1 table: {}".format(
                    ",".join(errors)
                )
            )
    except:
        raise


def put_sql_schedH1(data):
    """
    sql and db_transaction for update sched_h1 item
    """
    _sql = """UPDATE public.sched_h1
                SET 
                line_number = %s, 
                transaction_type_identifier = %s, 
                transaction_type = %s, 
                presidential_only = %s, 
                presidential_and_senate = %s, 
                senate_only = %s, 
                non_pres_and_non_senate = %s, 
                federal_percent = %s, 
                non_federal_percent = %s, 
                election_year = %s,
                administrative = %s,
                generic_voter_drive = %s, 
                public_communications = %s,
                last_update_date = %s
              WHERE transaction_id = %s AND report_id = %s AND cmte_id = %s 
              AND delete_ind is distinct from 'Y';
        """
    _v = (
        data.get("line_number"),
        data.get("transaction_type_identifier"),
        data.get("transaction_type"),
        data.get("presidential_only"),
        data.get("presidential_and_senate"),
        data.get("senate_only"),
        data.get("non_pres_and_non_senate"),
        data.get("federal_percent"),
        data.get("non_federal_percent"),
        data.get("election_year"),
        data.get("administrative"),
        data.get("generic_voter_drive"),
        data.get("public_communications"),
        datetime.datetime.now(),
        data.get("transaction_id"),
        data.get("report_id"),
        data.get("cmte_id"),
    )
    do_transaction(_sql, _v)


@new_report_date
def put_schedH1(data):
    """
    save/update a sched_h1 item

    here we are assuming entity_id are always referencing something already in our DB
    """
    try:
        check_mandatory_fields_SH1(data)
        # check_transaction_id(data.get('transaction_id'))
        try:
            put_sql_schedH1(data)
        except Exception as e:
            raise Exception(
                "The put_sql_schedH3 function is throwing an error: " + str(e)
            )
        return data
    except:
        raise


def validate_federal_nonfed_ratio(data):
    """
    validate fed and non_fed ratio add up:
    fed + non_fed == 100%
    e.g.
    0.45 + 0.55 == 1.00
    """
    if not (
            (
                    float(data.get("federal_percent")) + float(data.get("non_federal_percent"))
                    == float(1)
            )
    ):
        raise Exception("Error: combined federal and non-federal value should be 100%.")


def validate_sh1_data(data):
    """
    validate sh1 request data for db transaction
    """
    check_mandatory_fields_SH1(data)
    validate_federal_nonfed_ratio(data)


def election_year(report_id):
    """
    To get the election year from reports Table
    """
    try:
        # TODO: handle the case of report_id = 0
        # if not report_id:
        # return None
        with connection.cursor() as cursor:
            # Insert data into schedH3 table
            cursor.execute(
                """SELECT EXTRACT(YEAR FROM cvg_start_date) FROM public.reports WHERE report_id = %s""",
                [report_id],
            )
            election_year_tuple = cursor.fetchone()
            if election_year_tuple:
                return election_year_tuple[0]
            else:
                raise Exception(
                    "The report_id: {} does not exist in reports table.".format(
                        report_id
                    )
                )
    except Exception as err:
        raise Exception(f"election_year function is throwing an error: {err}")


def post_sql_schedH1(data):
    """
    save a new sched_h1 item
    """
    logger.debug("post sql h1 with data:{}".format(data))
    try:
        _sql = """
        INSERT INTO public.sched_h1 (
            cmte_id,
            report_id,
            line_number,
            transaction_type_identifier,
            transaction_type,
            transaction_id,
            presidential_only, 
            presidential_and_senate, 
            senate_only, 
            non_pres_and_non_senate, 
            federal_percent, 
            non_federal_percent, 
            election_year,
            administrative,
            generic_voter_drive, 
            public_communications,
            create_date
            )
        VALUES ({}); 
        """.format(
            ",".join(["%s"] * 17)
        )
        _v = (
            data.get("cmte_id"),
            data.get("report_id"),
            data.get("line_number"),
            data.get("transaction_type_identifier"),
            data.get("transaction_type"),
            data.get("transaction_id"),
            data.get("presidential_only"),
            data.get("presidential_and_senate"),
            data.get("senate_only"),
            data.get("non_pres_and_non_senate"),
            data.get("federal_percent"),
            data.get("non_federal_percent"),
            data.get("election_year"),
            data.get("administrative"),
            data.get("generic_voter_drive"),
            data.get("public_communications"),
            datetime.datetime.now(),
        )
        with connection.cursor() as cursor:
            # Insert data into schedH3 table
            cursor.execute(_sql, _v)
            logger.info("h1 saved.")
    except Exception:
        raise


@new_report_date
def post_schedH1(data):
    """
    save a new sched_h1 item
    """
    try:
        # check_mandatory_fields_SA(datum, MANDATORY_FIELDS_SCHED_A)
        data["transaction_id"] = get_next_transaction_id("SH")
        validate_sh1_data(data)
        try:
            post_sql_schedH1(data)
        except Exception as e:
            raise Exception(
                "The post_sql_schedH1 function is throwing an error: " + str(e)
            )
        return data
    except:
        raise


def get_schedH1(data):
    """
    load sched_h1 items
    """

    try:
        cmte_id = data.get("cmte_id")
        report_id = data.get("report_id")
        if "transaction_id" in data:
            transaction_id = check_transaction_id(data.get("transaction_id"))
            forms_obj = get_list_schedH1(report_id, cmte_id, transaction_id)
        else:
            forms_obj = get_list_all_schedH1(report_id, cmte_id)
        return forms_obj
    except:
        raise


def get_list_all_schedH1(report_id, cmte_id):
    """
    load all transactions for a report
    Note: for PTY, H1 is election year based
    """
    try:
        election_yr = election_year(report_id)
        with connection.cursor() as cursor:
            # GET single row from schedA table
            _sql = """SELECT json_agg(t) FROM ( SELECT
            cmte_id,
            report_id,
            line_number,
            transaction_type_identifier,
            transaction_type,
            transaction_id,
            presidential_only, 
            presidential_and_senate, 
            senate_only, 
            non_pres_and_non_senate, 
            federal_percent, 
            non_federal_percent, 
            election_year,
            administrative,
            generic_voter_drive, 
            public_communications,
            create_date ,
            last_update_date
            FROM public.sched_h1
            WHERE election_year = %s AND cmte_id = %s
            AND delete_ind is distinct from 'Y') t
            """
            cursor.execute(_sql, (election_yr, cmte_id))
            schedH1_list = cursor.fetchone()[0]
            if schedH1_list is None:
                raise NoOPError(
                    "No sched_H1 transaction found for report_id {} and cmte_id: {}".format(
                        report_id, cmte_id
                    )
                )
            merged_list = []
            for dictH1 in schedH1_list:
                merged_list.append(dictH1)
        return merged_list
    except Exception:
        raise


def get_list_schedH1(report_id, cmte_id, transaction_id):
    """
    load one transaction
    """
    try:
        with connection.cursor() as cursor:
            # GET single row from schedH3 table
            _sql = """SELECT json_agg(t) FROM ( SELECT
            cmte_id,
            report_id,
            line_number,
            transaction_type_identifier,
            transaction_type,
            transaction_id,
            presidential_only, 
            presidential_and_senate, 
            senate_only, 
            non_pres_and_non_senate, 
            federal_percent, 
            non_federal_percent, 
            election_year,
            administrative,
            generic_voter_drive, 
            public_communications,
            create_date ,
            last_update_date
            FROM public.sched_h1
            WHERE report_id = %s AND cmte_id = %s AND transaction_id = %s
            AND delete_ind is distinct from 'Y') t
            """
            cursor.execute(_sql, (report_id, cmte_id, transaction_id))
            schedH1_list = cursor.fetchone()[0]
            if schedH1_list is None:
                raise NoOPError(
                    "No sched_H1 transaction found for transaction_id {}".format(
                        transaction_id
                    )
                )
            merged_list = []
            for dictH1 in schedH1_list:
                merged_list.append(dictH1)
        return merged_list
    except Exception:
        raise


def delete_sql_schedH1(cmte_id, report_id, transaction_id):
    """
    do delete sql transaction
    """
    _sql = """
    UPDATE public.sched_h1
    SET delete_ind = 'Y' 
    WHERE transaction_id = %s AND report_id = %s AND cmte_id = %s
    """
    _v = (transaction_id, report_id, cmte_id)
    do_transaction(_sql, _v)


def delete_schedH1(data):
    """
    function for handling delete request for sh1
    """
    try:
        delete_sql_schedH1(
            data.get("cmte_id"), data.get("report_id"), data.get("transaction_id")
        )
    except Exception as e:
        raise


@api_view(["POST", "GET", "DELETE", "PUT"])
def schedH1(request):
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
                logger.debug("filtering and validating h1 data:{}".format(request.data))
                datum = schedH1_sql_dict(request.data)
                datum["report_id"] = report_id
                datum["cmte_id"] = cmte_id
                datum["transaction_type_identifier"] = "ALLOC_H1"
                # print('----')
                if (not report_id) or (report_id == "0"):
                    datum["election_year"] = None
                else:
                    datum["election_year"] = election_year(report_id)
                # print('....')
                if cmte_type(cmte_id) == "PTY":
                    datum["administrative"] = True
                    datum["generic_voter_drive"] = True
                    datum["public_communications"] = True

                if "transaction_id" in request.data and check_null_value(
                        request.data.get("transaction_id")
                ):
                    datum["transaction_id"] = check_transaction_id(
                        request.data.get("transaction_id")
                    )
                    data = put_schedH1(datum)
                else:
                    # print(datum)
                    logger.debug("h1 data after validation:{}".format(datum))
                    data = post_schedH1(datum)
                # Associating child transactions to parent and storing them to DB

                output = get_schedH1(data)
                return JsonResponse(output[0], status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response(
                    "The schedH1 API - POST is throwing an exception: " + str(e),
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
                datum = get_schedH1(data)
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
                    "The schedH1 API - GET is throwing an error: " + str(e),
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
                delete_schedH1(data)
                return Response(
                    "The Transaction ID: {} has been successfully deleted".format(
                        data.get("transaction_id")
                    ),
                    status=status.HTTP_201_CREATED,
                )
            except Exception as e:
                return Response(
                    "The schedH1 API - DELETE is throwing an error: " + str(e),
                    status=status.HTTP_400_BAD_REQUEST,
                )

        elif request.method == "PUT":
            try:
                cmte_id = get_comittee_id(request.user.username)
                datum = schedH1_sql_dict(request.data)
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
                datum["cmte_id"] = cmte_id
                datum["transaction_type_identifier"] = "ALLOC_H1"
                # print('----')
                if (not report_id) or (report_id == "0"):
                    datum["election_year"] = None
                else:
                    datum["election_year"] = int(election_year(report_id))
                # print('....')
                if cmte_type(cmte_id) == "PTY":
                    datum["administrative"] = True
                    datum["generic_voter_drive"] = True
                    datum["public_communications"] = True

                # if 'entity_id' in request.data and check_null_value(request.data.get('entity_id')):
                #     datum['entity_id'] = request.data.get('entity_id')
                # if request.data.get('transaction_type') in CHILD_SCHED_B_TYPES:
                #     data = put_schedB(datum)
                #     output = get_schedB(data)
                # else:
                data = put_schedH1(datum)
                # output = get_schedA(data)
                return JsonResponse(data, status=status.HTTP_201_CREATED)
            except Exception as e:
                logger.debug(e)
                return Response(
                    "The schedH1 API - PUT is throwing an error: " + str(e),
                    status=status.HTTP_400_BAD_REQUEST,
                )
    except Exception as e:
        json_result = {'message': str(e)}
        return JsonResponse(json_result, status=status.HTTP_403_FORBIDDEN, safe=False)


@api_view(["GET"])
def validate_h1_h2_exist(request):
    """
    validate h1 or h2 exist or not - used to enable h3/h5 warning message
    
    """

    logger.debug("validate h1/h2 exist with request:{}".format(request.query_params))
    try:
        cmte_id = get_comittee_id(request.user.username)
        report_id = request.query_params.get("report_id")
        cmte_type_category = request.query_params.get("cmte_type_category")
        calendar_year = check_calendar_year(request.query_params.get("calendar_year"))
        start_dt = datetime.date(int(calendar_year), 1, 1)
        end_dt = datetime.date(int(calendar_year), 12, 31)
        activity_event_type = request.query_params.get("activity_event_type")
        # event_name = request.query_params.get('activity_event_identifier')
        # transaction_type_identifier = request.query_params.get('transaction_type_identifier')
        _count = 0

        if activity_event_type in ["DF", "DC"]:  # event-based, goes to h2
            _sql = """
            select count(*)
            from public.sched_h2 
            where cmte_id = %s 
            and report_id = %s
            and delete_ind is distinct from 'Y'
            """
            add_on = ""
            if activity_event_type == "DF":
                add_on = "and fundraising is true"
            else:
                add_on = "and direct_cand_support is true"

            with connection.cursor() as cursor:
                logger.debug("query with _sql:{}".format(_sql))
                # logger.debug('query with {}, {}, {}, {}'.format(cmte_id, event_name, start_dt, end_dt))
                cursor.execute(_sql + add_on, (cmte_id, report_id))
                if not cursor.rowcount:
                    raise Exception("Error: something warong with db query.")
                _count = int(cursor.fetchone()[0])

            # _sql = """
            # select activity_event_amount_ytd
            # from public.sched_h4
            # where cmte_id = %s
            # and activity_event_identifier = %s
            # and create_date between %s and %s
            # and delete_ind is distinct from 'Y'
            # order by create_date desc, last_update_date desc;
            # """
            # with connection.cursor() as cursor:
            #     cursor.execute(_sql, (cmte_id, event_name, start_dt, end_dt))
            #     if not cursor.rowcount:
            #         aggregate_amount = 0
            #     else:
            #         aggregate_amount = float(cursor.fetchone()[0])

        else:  # need to go to h1 for ratios
            # activity_event_type = request.query_params.get('activity_event_type')

            # if not activity_event_type:
            #     raise Exception('Error: event type is required.')

            if cmte_type_category == "PTY":
                # _sql = """
                # select federal_percent from public.sched_h1
                # where election_year = %s
                # and cmte_id = %s
                # and report_id = %s
                # and delete_ind is distinct from 'Y'
                # order by create_date desc, last_update_date desc
                # """
                _sql = """
                select count(*) from public.sched_h1
                where election_year = %s
                and cmte_id = %s
                and delete_ind is distinct from 'Y'
                """
                logger.debug("sql for query h1:{}".format(_sql))
                with connection.cursor() as cursor:
                    cursor.execute(_sql, (calendar_year, cmte_id))
                    if not cursor.rowcount:
                        raise Exception("Error: no valid h1 data found.")
                    _count = int(cursor.fetchone()[0])
            elif cmte_type_category == "PAC":
                # activity_event_type = request.query_params.get('activity_event_type')
                # if not activity_event_type:
                # return Response('Error: event type is required for this committee.')
                event_type_code = {
                    "AD": "administrative",  # TODO: need to fix this typo
                    "GV": "generic_voter_drive",
                    "PC": "public_communications",
                }
                h1_event_type = event_type_code.get(activity_event_type)
                if not h1_event_type:
                    return Response("Error: activity type not valid")
                _sql = """
                select count(*) from public.sched_h1
                where election_year = %s
                and cmte_id = %s
                and report_id = %s
                """
                activity_part = """and {} = true """.format(h1_event_type)
                # order_part = 'order by create_date desc, last_update_date desc'
                _sql = _sql + activity_part
                logger.debug("sql for query h1:{}".format(_sql))
                with connection.cursor() as cursor:
                    cursor.execute(_sql, (calendar_year, cmte_id, report_id))
                    if not cursor.rowcount:
                        raise Exception("Error: no valid h1 data found.")
                    _count = int(cursor.fetchone()[0])
            else:
                raise Exception("invalid cmte_type_category.")

        #     _sql = """
        #         select activity_event_amount_ytd
        #         from public.sched_h4
        #         where cmte_id = %s
        #         and activity_event_type = %s
        #         and create_date between %s and %s
        #         order by create_date desc, last_update_date desc
        #     """
        #     with connection.cursor() as cursor:
        #         cursor.execute(_sql, (cmte_id, activity_event_type, start_dt, end_dt))
        #         if not cursor.rowcount:
        #             aggregate_amount = 0
        #         else:
        #             aggregate_amount = float(cursor.fetchone()[0])
        # # fed_percent = float(cursor.fetchone()[0])
        # fed_share = float(total_amount) * fed_percent
        # nonfed_share = float(total_amount) - fed_share
        # if transaction_type_identifier and not transaction_type_identifier.endswith('_MEMO'):
        #     new_aggregate_amount = aggregate_amount + float(total_amount)
        # else:
        #     new_aggregate_amount = aggregate_amount
        return JsonResponse({"count": _count}, status=status.HTTP_200_OK)
    except:
        raise


@api_view(["GET"])
def validate_pac_h1(request):
    """
    api to validate h1 status
    """
    try:
        cmte_id = get_comittee_id(request.user.username)
        report_id = request.query_params.get("report_id")
        event_types = [
            "administrative",  # TODO: need to fix this typo
            "generic_voter_drive",
            "public_communications",
        ]
        _result = {}
        for _event_type in event_types:
            with connection.cursor() as cursor:
                _sql = """
                select count(*) from public.sched_h1
                where cmte_id = '{}'
                and report_id = {}
                and {} = true
                and delete_ind is distinct from 'Y'
                """.format(
                    cmte_id, report_id, _event_type
                )
                cursor.execute(_sql)
                if not cursor.rowcount:
                    raise Exception("Error: exceptions when query pac h1 data.")
                _count = int(cursor.fetchone()[0])
                _result.update({_event_type: _count})
        return JsonResponse(_result, status=status.HTTP_200_OK)
    except:
        raise


def get_old_amount(transaction_id):
    """
    helper function for loading total_amount
    """
    _sql = """
    SELECT transaction_amount,
    aggregation_ind
    FROM public.all_other_transactions_view
    WHERE transaction_id = %s
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(_sql, [transaction_id])
            if cursor.rowcount:
                row_data = cursor.fetchone()
                return row_data[0], row_data[1]
            return 0
    except:
        raise


@api_view(["GET"])
def get_fed_nonfed_share(request):
    """
    get calendar year fed_nonfed share percentage, also query aggregation
    and update aggregation value.

    if event_name is available:
        go to h2 for ration
        grab event-based aggregation value from h4
    else:
        go to h1 for ratio
            if party, get election_year based fixed ratio
            if PAC, get activity based ratio
        grad event_type-based aggregation value from h4
    calculate fed and non-fed share based on ratio and update aggregate value

    update 20191112: 'election year' added to table - calendar year will match to
    election_year in db. 
    """

    logger.debug("get_fed_nonfed_share with request:{}".format(request.query_params))
    try:
        cmte_id = get_comittee_id(request.user.username)
        report_id = request.query_params.get("report_id")
        transaction_id = request.query_params.get("transaction_id")

        if transaction_id and not transaction_id.startswith("SH"):
            transaction_id = None

        # for Memo tranasctions, we query parent aggregate amount instead
        back_ref_transaction_id = request.query_params.get("back_ref_transaction_id")
        if transaction_id and not transaction_id.startswith("SH"):
            back_ref_transaction_id = None
        # print(transaction_id)
        # if 'old_amount' in request.query_params:
        #     old_amount = float(request.query_params.get('old_amount'))
        # else:
        #     old_amount = 0

        # for editing purpose, need grab old amount
        old_amount = 0
        aggregation_ind = "Y"
        if transaction_id:
            old_amount, aggregation_ind = get_old_amount(transaction_id)
        old_amount = float(old_amount)

        cmte_type_category = request.query_params.get("cmte_type_category")
        total_amount = request.query_params.get("total_amount")
        calendar_year = check_calendar_year(request.query_params.get("calendar_year"))
        start_dt = datetime.date(int(calendar_year), 1, 1)
        end_dt = datetime.date(int(calendar_year), 12, 31)
        event_name = request.query_params.get("activity_event_identifier")
        transaction_type_identifier = request.query_params.get(
            "transaction_type_identifier"
        )
        if transaction_type_identifier.startswith("ALLOC_FEA"):
            tran_tbl = "public.sched_h6"
            f_ytd = "activity_event_total_ytd"
            f_event = "account_event_identifier"
        else:
            tran_tbl = "public.sched_h4"
            f_ytd = "activity_event_amount_ytd"
            f_event = "activity_event_identifier"

        if event_name:  # event-based, goes to h2
            _sql = """
            select federal_percent 
            from public.sched_h2 
            where cmte_id = %s 
            and report_id = %s
            and activity_event_name = %s
            and delete_ind is distinct from 'Y'
            order by create_date desc, last_update_date desc;
            """
            with connection.cursor() as cursor:
                logger.debug("query with _sql:{}".format(_sql))
                logger.debug(
                    "query with {}, {}, {}, {}".format(
                        cmte_id, event_name, start_dt, end_dt
                    )
                )
                cursor.execute(_sql, (cmte_id, report_id, event_name))
                if not cursor.rowcount:
                    raise Exception("Error: no h2 data found.")
                fed_percent = float(cursor.fetchone()[0])

            # for esiting, just grab the aggregation amount
            if transaction_id:
                _sql = """
                select {} 
                from {}
                where transaction_id = %s
                """.format(
                    f_ytd, tran_tbl
                )
                with connection.cursor() as cursor:
                    cursor.execute(_sql, [transaction_id])
                    if not cursor.rowcount:
                        aggregate_amount = 0
                    else:
                        aggregate_amount = float(cursor.fetchone()[0])
            elif back_ref_transaction_id:
                _sql = """
                select {} 
                from {}
                where transaction_id = %s
                """.format(
                    f_ytd, tran_tbl
                )
                with connection.cursor() as cursor:
                    cursor.execute(_sql, [back_ref_transaction_id])
                    if not cursor.rowcount:
                        aggregate_amount = 0
                    else:
                        aggregate_amount = float(cursor.fetchone()[0])
            else:
                _sql = """
                select {} 
                from {} 
                where cmte_id = %s 
                and {} = %s
                and create_date between %s and %s
                and delete_ind is distinct from 'Y'
                order by expenditure_date desc, last_update_date desc;
                """.format(
                    f_ytd, tran_tbl, f_event
                )
                with connection.cursor() as cursor:
                    cursor.execute(_sql, (cmte_id, event_name, start_dt, end_dt))
                    if not cursor.rowcount:
                        aggregate_amount = 0
                    else:
                        aggregate_amount = float(cursor.fetchone()[0])

        else:  # need to go to h1 for ratios
            activity_event_type = request.query_params.get("activity_event_type")

            if not activity_event_type:
                raise Exception("Error: event type is required.")

            if cmte_type_category == "PTY":
                # _sql = """
                # select federal_percent from public.sched_h1
                # where election_year = %s
                # and cmte_id = %s
                # and report_id = %s
                # and delete_ind is distinct from 'Y'
                # order by create_date desc, last_update_date desc
                # """
                _sql = """
                select federal_percent 
                from public.sched_h1
                where election_year = %s
                and cmte_id = %s
                and delete_ind is distinct from 'Y'
                order by create_date desc, last_update_date desc
                """
                logger.debug("sql for query h1:{}".format(_sql))
                with connection.cursor() as cursor:
                    cursor.execute(_sql, (calendar_year, cmte_id))
                    if not cursor.rowcount:
                        raise Exception("Error: no h1 data found.")
                    fed_percent = float(cursor.fetchone()[0])
            elif cmte_type_category == "PAC":
                # activity_event_type = request.query_params.get('activity_event_type')
                # if not activity_event_type:
                # return Response('Error: event type is required for this committee.')
                event_type_code = {
                    "AD": "administrative",  # TODO: need to fix this typo
                    "GV": "generic_voter_drive",
                    "PC": "public_communications",
                }
                h1_event_type = event_type_code.get(activity_event_type)
                if not h1_event_type:
                    return Response("Error: activity type not valid")
                _sql = """
                select federal_percent from public.sched_h1
                where election_year = %s
                and cmte_id = %s
                and report_id = %s
                """
                activity_part = """and {} = true """.format(h1_event_type)
                order_part = "order by create_date desc, last_update_date desc"
                _sql = _sql + activity_part + order_part
                logger.debug("sql for query h1:{}".format(_sql))
                with connection.cursor() as cursor:
                    cursor.execute(_sql, (calendar_year, cmte_id, report_id))
                    if not cursor.rowcount:
                        raise Exception("Error: no h1 data found.")
                    fed_percent = float(cursor.fetchone()[0])
            else:
                raise Exception("invalid cmte_type_category.")

            if transaction_id:
                _sql = """
                select {} 
                from {} 
                where transaction_id = %s
                """.format(
                    f_ytd, tran_tbl
                )
                with connection.cursor() as cursor:
                    cursor.execute(_sql, [transaction_id])
                    if not cursor.rowcount:
                        aggregate_amount = 0
                    else:
                        aggregate_amount = float(cursor.fetchone()[0])
            elif back_ref_transaction_id:
                _sql = """
                select {} 
                from {} 
                where transaction_id = %s
                """.format(
                    f_ytd, tran_tbl
                )
                with connection.cursor() as cursor:
                    cursor.execute(_sql, [back_ref_transaction_id])
                    if not cursor.rowcount:
                        aggregate_amount = 0
                    else:
                        aggregate_amount = float(cursor.fetchone()[0])
            else:
                _sql = """
                select {} 
                from {} 
                where cmte_id = %s 
                and activity_event_type = %s
                and expenditure_date between %s and %s
                and delete_ind is distinct from 'Y'
                order by expenditure_date desc, last_update_date desc
                """.format(
                    f_ytd, tran_tbl
                )
                print("...")
                print(_sql)
                with connection.cursor() as cursor:
                    cursor.execute(
                        _sql, (cmte_id, activity_event_type, start_dt, end_dt)
                    )
                    # logger.debug()
                    if not cursor.rowcount:
                        aggregate_amount = 0
                    else:
                        aggregate_amount = float(cursor.fetchone()[0])
        # fed_percent = float(cursor.fetchone()[0])
        # print(aggregate_amount)
        logger.debug("aggregate_amount loaded:{}".format(aggregate_amount))
        fed_share = float(total_amount) * fed_percent
        nonfed_share = float(total_amount) - fed_share
        if transaction_type_identifier and aggregation_ind == "N":
            new_aggregate_amount = aggregate_amount
        else:
            new_aggregate_amount = aggregate_amount + float(total_amount) - old_amount
            # new_aggregate_amount = aggregate_amount
        return JsonResponse(
            {
                "fed_share": "{0:.2f}".format(fed_share),
                "nonfed_share": "{0:.2f}".format(nonfed_share),
                "aggregate_amount": "{0:.2f}".format(new_aggregate_amount),
            },
            status=status.HTTP_200_OK,
        )
    except:
        raise


@api_view(["GET"])
def get_h1_percentage(request):
    """
    get calendar year fed_nonfed share percentage
    """
    logger.debug("get_h1_percentage with request:{}".format(request.query_params))
    try:
        cmte_id = get_comittee_id(request.user.username)

        # if not('report_id' in request.query_params and check_null_value(request.query_params.get('report_id'))):
        # raise Exception ('Missing Input: report_id is mandatory')

        if not (
                "calendar_year" in request.query_params
                and check_null_value(request.query_params.get("calendar_year"))
        ):
            raise Exception("Missing Input: calendar_year is mandatory")
        calendar_year = check_calendar_year(request.query_params.get("calendar_year"))
        # start_dt = datetime.date(int(calendar_year), 1, 1)
        # end_dt = datetime.date(int(calendar_year), 12, 31)
        _sql = """
            select json_agg(t) from
            (select federal_percent, non_federal_percent from public.sched_h1
            where election_year = %s
            and cmte_id = %s
            order by create_date desc, last_update_date desc) t
        """
        with connection.cursor() as cursor:
            cursor.execute(_sql, (calendar_year, cmte_id))
            # print('rows:{}'.format(cursor.rowcount))
            json_data = cursor.fetchone()[0]
            # print(json_data)
            if not json_data:
                # raise Exception('Error: no h1 found.')
                return Response(
                    "The schedH1 API - PUT is throwing an error: no h1 data found.",
                    status=status.HTTP_400_BAD_REQUEST,
                )
        return JsonResponse(json_data[0], status=status.HTTP_200_OK)
    except:
        raise


"""
SCHED_H2:
Ratios for Allocable Fundraising Events and Direct Candidate Support 
"""


def schedH2_sql_dict(data):
    """
    filter out valid fileds for sched_H1
    """
    valid_h2_fields = [
        # "line_number",
        "transaction_type_identifier",
        # "transaction_type",
        "activity_event_name",
        "fundraising",
        "direct_cand_support",
        "ratio_code",
        "revise_date",
        "federal_percent",
        "non_federal_percent",
    ]
    try:
        # return {k: v for k, v in data.items() if k in valid_h2_fields}
        datum = {k: v for k, v in data.items() if k in valid_h2_fields}
        if "receipt_date" in data:
            datum["revise_date"] = data.get("receipt_date")
        datum["line_number"], datum["transaction_type"] = get_line_number_trans_type(
            data.get("transaction_type_identifier")
        )
        return datum
    except:
        raise Exception("invalid h2 request data.")


def check_mandatory_fields_SH2(data):
    """
    check madatroy frields for sh1
    """
    try:
        errors = []
        for field in MANDATORY_FIELDS_SCHED_H2:
            if not (field in data and check_null_value(data.get(field))):
                errors.append(field)
        if errors:
            raise Exception(
                "The following mandatory fields are required in order to save data to schedH2 table: {}".format(
                    ",".join(errors)
                )
            )
    except:
        raise


def put_sql_schedH2(data):
    """
    sql and db_transaction for update sched_h1 item
    """
    _sql = """UPDATE public.sched_h2
            SET 
                line_number = %s, 
                transaction_type_identifier = %s, 
                transaction_type = %s,
                activity_event_name = %s,
                fundraising = %s,
                direct_cand_support = %s,
                ratio_code = %s,
                revise_date = %s,
                federal_percent = %s,
                non_federal_percent = %s,
                last_update_date = %s
            WHERE transaction_id = %s AND report_id = %s AND cmte_id = %s 
            AND delete_ind is distinct from 'Y';
        """
    _v = (
        data.get("line_number"),
        data.get("transaction_type_identifier"),
        data.get("transaction_type"),
        data.get("activity_event_name"),
        data.get("fundraising"),
        data.get("direct_cand_support"),
        data.get("ratio_code"),
        data.get("revise_date"),
        data.get("federal_percent"),
        data.get("non_federal_percent"),
        datetime.datetime.now(),
        data.get("transaction_id"),
        data.get("report_id"),
        data.get("cmte_id"),
    )
    do_transaction(_sql, _v)


@new_report_date
def put_schedH2(data):
    """
    save/update a sched_h2 item

    here we are assuming entity_id are always 
    referencing something already in our DB
    """
    try:
        # check_mandatory_fields_SH2(data)
        validate_sh2_data(data)
        # check_transaction_id(data.get('transaction_id'))
        try:
            put_sql_schedH2(data)
        except Exception as e:
            raise Exception(
                "The put_sql_schedH2 function is throwing an error: " + str(e)
            )
        return data
    except:
        raise


def validate_sh2_data(data):
    """
    validate sh1 request data for db transaction
    """
    check_mandatory_fields_SH2(data)
    validate_federal_nonfed_ratio(data)


def post_sql_schedH2(data):
    """
    save a new sched_h1 item
    """
    try:
        _sql = """
        INSERT INTO public.sched_h2 (
            cmte_id,
            report_id,
            line_number,
            transaction_type_identifier,
            transaction_type,
            transaction_id,
            activity_event_name,
            fundraising,
            direct_cand_support,
            ratio_code,
            revise_date,
            federal_percent,
            non_federal_percent,
            create_date
            )
        VALUES ({}); 
        """.format(
            ",".join(["%s"] * 14)
        )
        _v = (
            data.get("cmte_id"),
            data.get("report_id"),
            data.get("line_number"),
            data.get("transaction_type_identifier"),
            data.get("transaction_type"),
            data.get("transaction_id"),
            data.get("activity_event_name"),
            data.get("fundraising"),
            data.get("direct_cand_support"),
            data.get("ratio_code"),
            data.get("revise_date"),
            data.get("federal_percent"),
            data.get("non_federal_percent"),
            datetime.datetime.now(),
        )
        with connection.cursor() as cursor:
            # Insert data into schedH3 table
            cursor.execute(_sql, _v)
    except Exception:
        raise


@new_report_date
def post_schedH2(data):
    """
    save a new sched_h1 item
    """
    try:
        # check_mandatory_fields_SA(datum, MANDATORY_FIELDS_SCHED_A)
        data["transaction_id"] = get_next_transaction_id("SH")
        validate_sh2_data(data)
        try:
            post_sql_schedH2(data)
        except Exception as e:
            raise Exception(
                "The post_sql_schedH2 function is throwing an error: " + str(e)
            )
        return data
    except:
        raise


def get_schedH2(data):
    """
    load sched_h1 items
    """

    try:
        cmte_id = data.get("cmte_id")
        report_id = data.get("report_id")
        if "transaction_id" in data:
            transaction_id = check_transaction_id(data.get("transaction_id"))
            forms_obj = get_list_schedH2(report_id, cmte_id, transaction_id)
        else:
            forms_obj = get_list_all_schedH2(report_id, cmte_id)
        return forms_obj
    except:
        raise


def get_list_all_schedH2(report_id, cmte_id):
    """
    load all transactions for a report
    revise_date is renamed to 'receipt_date' in front end
    """
    try:
        with connection.cursor() as cursor:
            # GET single row from schedA table
            _sql = """SELECT json_agg(t) FROM ( SELECT
            cmte_id,
            report_id,
            line_number,
            transaction_type_identifier,
            transaction_type,
            transaction_id,
            activity_event_name,
            fundraising,
            direct_cand_support,
            ratio_code,
            revise_date as receipt_date,
            federal_percent,
            non_federal_percent,
            create_date ,
            last_update_date
            FROM public.sched_h2
            WHERE report_id = %s AND cmte_id = %s
            AND delete_ind is distinct from 'Y') t
            """
            cursor.execute(_sql, (report_id, cmte_id))
            schedH_list = cursor.fetchone()[0]
            if schedH_list is None:
                raise NoOPError(
                    "No sched_H2 transaction found for report_id {} and cmte_id: {}".format(
                        report_id, cmte_id
                    )
                )
            merged_list = []
            for dictH in schedH_list:
                merged_list.append(dictH)
        return merged_list
    except Exception:
        raise


def get_list_schedH2(report_id, cmte_id, transaction_id):
    """
    load one transaction
    """
    try:
        with connection.cursor() as cursor:
            # GET single row from schedH3 table
            _sql = """SELECT json_agg(t) FROM ( SELECT
            cmte_id,
            report_id,
            line_number,
            transaction_type_identifier,
            transaction_type,
            transaction_id,
            activity_event_name,
            ( CASE fundraising 
            WHEN true THEN 'fundraising' 
            ELSE 'direct_cand_suppot' 
            END )  AS event_type, 
            fundraising,
            direct_cand_support,
            ratio_code,
            revise_date as receipt_date,
            federal_percent,
            non_federal_percent,
            create_date ,
            last_update_date
            FROM public.sched_h2
            WHERE report_id = %s AND cmte_id = %s AND transaction_id = %s
            AND delete_ind is distinct from 'Y') t
            """
            cursor.execute(_sql, (report_id, cmte_id, transaction_id))
            schedH_list = cursor.fetchone()[0]
            if schedH_list is None:
                raise NoOPError(
                    "No sched_H2 transaction found for transaction_id {}".format(
                        transaction_id
                    )
                )
            merged_list = []
            for dictH in schedH_list:
                merged_list.append(dictH)
        return merged_list
    except Exception:
        raise


def delete_sql_schedH2(cmte_id, report_id, transaction_id):
    """
    do delete sql transaction
    """
    _sql = """
    UPDATE public.sched_h2
    SET delete_ind = 'Y' 
    WHERE transaction_id = %s AND report_id = %s AND cmte_id = %s
    """
    _v = (transaction_id, report_id, cmte_id)
    do_transaction(_sql, _v)


def delete_schedH2(data):
    """
    function for handling delete request for sh1
    """
    try:
        delete_sql_schedH2(
            data.get("cmte_id"), data.get("report_id"), data.get("transaction_id")
        )
    except Exception as e:
        raise


@api_view(["GET"])
def get_h2_type_events(request):
    """
    load all event names for each category(direct cand support or 
    fundraising) to populate events dropdown list
    """
    logger.debug("get_h2_type_events with request:{}".format(request.query_params))
    cmte_id = get_comittee_id(request.user.username)
    event_type = request.query_params.get("activity_event_type").strip()
    report_id = request.query_params.get("report_id").strip()
    if event_type not in ["fundraising", "direct_cand_support"]:
        raise Exception("missing or non-valid event type value")
    if event_type == "fundraising":
        _sql = """
        SELECT json_agg(t) from (
        SELECT activity_event_name 
        FROM   public.sched_h2 
        WHERE  cmte_id = %s
        AND report_id = %s
        AND fundraising = true
        AND delete_ind is distinct from 'Y') t
        """
    else:
        _sql = """
        SELECT json_agg(t) from(
        SELECT activity_event_name 
        FROM   public.sched_h2 
        WHERE  cmte_id = %s 
        AND report_id = %s
        AND direct_cand_support = true
        AND delete_ind is distinct from 'Y') t
        """
    try:
        with connection.cursor() as cursor:
            logger.debug("query with _sql:{}".format(_sql))
            cursor.execute(_sql, [cmte_id, report_id])
            json_res = cursor.fetchone()[0]
            # print(json_res)
            if not json_res:
                return Response([], status=status.HTTP_200_OK)
        # calendar_year = check_calendar_year(request.query_params.get('calendar_year'))
        # start_dt = datetime.date(int(calendar_year), 1, 1)
        # end_dt = datetime.date(int(calendar_year), 12, 31)
        return Response(json_res, status=status.HTTP_200_OK)
    except:
        raise


def is_new_report(report_id, cmte_id):
    """
    check if a report_id is new or not
    a report_id is new if:
    1.  not exist in sched_h2 table 
    2. and the cvg_date is newer than the most recent one

    TODO: may need to reconsider this
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
            JOIN PUBLIC.sched_h2 sh 
                ON r.report_id = sh.report_id 
                    AND r.cmte_id = sh.cmte_id 
                    AND r.cmte_id = %s
        ORDER  BY seq 
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(_sql, (report_id, cmte_id))
            results = cursor.fetchall()
            new_date = results[0][1]
            if len(results) != 2:  # no old max date found
                return False
            else:
                old_date = results[1][1]
                if new_date and old_date and new_date > old_date:
                    return True
            return False
    except:
        raise


def do_h2_carryover(report_id, cmte_id):
    """
    this is the function to handle h2 carryover form one report to next report:
    1. load all h2 items with distinct event names from last report
    2. update all records with new transaction_id, new report_id
    3. set ration code to 's' - same as previously
    4. copy all other fields
    """
    _sql = """
    insert into public.sched_h2(
                    cmte_id,
                    report_id,
                    line_number,
                    transaction_type_identifier,
                    transaction_type,
                    transaction_id,
                    activity_event_name,
                    fundraising,
                    direct_cand_support,
                    ratio_code,
                    revise_date,
                    federal_percent,
                    non_federal_percent,
                    back_ref_transaction_id,
                    create_date,
                    last_update_date
					)
					SELECT 
					h.cmte_id, 
                    %s, 
                    h.line_number,
                    h.transaction_type_identifier, 
                    h.transaction_type,
                    get_next_transaction_id('SH'), 
                    h.activity_event_name,
                    h.fundraising,
                    h.direct_cand_support, 
                    's',
                    h.revise_date,
                    h.federal_percent,
                    h.non_federal_percent,
                    h.transaction_id,
                    h.create_date,
                    now()
            FROM public.sched_h2 h, public.reports r
            WHERE 
            h.cmte_id = %s
            AND h.report_id != %s
            AND h.report_id = r.report_id
            AND r.cvg_start_date < (
                        SELECT r.cvg_start_date
                        FROM   public.reports r
                        WHERE  r.report_id = %s
                    )
            AND h.transaction_id NOT In (
                select distinct h2.back_ref_transaction_id from public.sched_h2 h2
                where h2.cmte_id = %s
                and h2.back_ref_transaction_id is not null
            )
            AND h.delete_ind is distinct from 'Y'
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(_sql, (report_id, cmte_id, report_id, report_id, cmte_id))
            if cursor.rowcount == 0:
                logger.debug("No valid h2 items found.")
            logger.debug("h2 carryover done with report_id {}".format(report_id))
            logger.debug("total carryover h2 items:{}".format(cursor.rowcount))
    except:
        raise


@api_view(["GET"])
def get_h2_summary_table(request):
    """
    h2 summary need to be h4 transaction-based:
    all the calendar-year based h2 need to show up for current report as long as
    a live h4 transaction refering this h2 exist:
    h2 report goes with h4/h3 transactions, not h2 report_id

    update: all h2 items with current report_id need to show up
    """

    logger.debug("get_h2_summary_table with request:{}".format(request.query_params))
    _sql = """
    SELECT json_agg(t) from(
    SELECT activity_event_name, 
        ( CASE fundraising 
            WHEN true THEN 'fundraising' 
            ELSE 'direct_cand_suppot' 
            END )  AS event_type, 
        revise_date AS receipt_date, 
        ratio_code, 
        federal_percent, 
        non_federal_percent,
        transaction_id
    FROM   public.sched_h2 
    WHERE  cmte_id = %s AND report_id = %s AND delete_ind is distinct from 'Y'
        AND activity_event_name IN (
            SELECT activity_event_identifier 
            FROM   public.sched_h4 
            WHERE  report_id = %s
            AND cmte_id = %s)
    UNION SELECT activity_event_name, 
        ( CASE fundraising 
            WHEN true THEN 'fundraising' 
            ELSE 'direct_cand_suppot' 
            END )  AS event_type, 
        revise_date AS receipt_date, 
        ratio_code, 
        federal_percent, 
        non_federal_percent,
        transaction_id
    FROM   public.sched_h2 
    WHERE  cmte_id = %s AND report_id = %s AND delete_ind is distinct from 'Y'
        AND activity_event_name IN (
            SELECT activity_event_name 
            FROM   public.sched_h3 
            WHERE  report_id = %s
            AND cmte_id = %s)
    UNION SELECT activity_event_name, 
        ( CASE fundraising 
            WHEN true THEN 'fundraising' 
            ELSE 'direct_cand_suppot' 
            END )  AS event_type, 
        revise_date AS receipt_date, 
        ratio_code, 
        federal_percent, 
        non_federal_percent,
        transaction_id 
    FROM   public.sched_h2 
    WHERE  cmte_id = %s AND report_id = %s AND ratio_code = 'n' AND delete_ind is distinct from 'Y'
            ) t;
    """
    try:
    #: Get the request parameters and set for Pagination
        query_params = request.query_params
        page_num = get_int_value(query_params.get("page"))

        descending = query_params.get("descending")
        if not (
            "sortColumnName" in query_params
            and check_null_value(query_params.get("sortColumnName"))
        ):
            sortcolumn = "name"
        elif query_params.get("sortColumnName") == "default":
            sortcolumn = "name"
        else:
            sortcolumn = query_params.get("sortColumnName")
        itemsperpage =  get_int_value(query_params.get("itemsPerPage"))
        search_string = query_params.get("search")
        params = query_params.get("filters", {})
        keywords = params.get("keywords")
        if str(descending).lower() == "true":
            descending = "DESC"
        else:
            descending = "ASC"
        trans_query_string_count = ""

        #: Hardcode cmte value for now and remove after dev complete
        #cmte_id = "C00000935"
        cmte_id = get_comittee_id(request.user.username)
        report_id = request.query_params.get("report_id")
        # logger.debug('checking if it is a new report')
        # if is_new_report(report_id, cmte_id):
        logger.debug("check and do h2 carryover.")
        do_h2_carryover(report_id, cmte_id)
        with connection.cursor() as cursor:
            logger.debug("query with _sql:{}".format(_sql))
            logger.debug(
                "query with cmte_id:{}, report_id:{}".format(cmte_id, report_id)
            )
            cursor.execute(
                _sql,
                (
                    cmte_id,
                    report_id,
                    report_id,
                    cmte_id,
                    cmte_id,
                    report_id,
                    report_id,
                    cmte_id,
                    cmte_id,
                    report_id,
                ),
            )
            json_res = cursor.fetchone()[0]
            # print(json_res)
            if not json_res:
                return Response([], status=status.HTTP_200_OK)
            for _rec in json_res:
                _rec["trashable"] = False
                if _rec["ratio_code"] == "n":
                    if (
                            count_h2_transactions(
                                cmte_id, report_id, _rec["activity_event_name"]
                            )
                            == 0
                    ):
                        _rec["trashable"] = True
                # else:
                #     _rec['trashable'] - False

                # 'Error: no valid h2 data found for this report.')
        # calendar_year = check_calendar_year(request.query_params.get('calendar_year'))
        # start_dt = datetime.date(int(calendar_year), 1, 1)
        # end_dt = datetime.date(int(calendar_year), 12, 31)
        

# : insert pagination functionality

            '''total_count = len(json_res)
            paginator = Paginator(json_res, itemsperpage)
            if paginator.num_pages < page_num:
                page_num = paginator.num_pages
            json_res = paginator.page(page_num)
            json_result = {
                "transactions": list(json_res),
                "totaltransactionsCount": total_count,
                "itemsPerPage": itemsperpage,
                "pageNumber": page_num,
                "totalPages": paginator.num_pages,
            }
            '''
            json_result = get_pagination_dataset(json_res, itemsperpage, page_num)
            return Response(json_result, status=status.HTTP_200_OK)
    except:
        raise
#: get the paginator page with other details like  
def get_pagination_dataset(json_res, itemsperpage, page_num):
    if check_null_value(json_res) is False  or json_res is None:
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


def count_h2_transactions(cmte_id, report_id, activity_event_name):
    """
    helpfer function for counting current h2 assoicated transactions
    """
    _sql = """
    select count(*) 
    from all_other_transactions_view 
    where activity_event_identifier = %s
    and cmte_id = %s 
    and report_id = %s
    and delete_ind is distinct from 'Y'
    """
    try:
        with connection.cursor() as cursor:
            logger.debug("count_h2_transactions with _sql:{}".format(_sql))

            logger.debug(
                "query with cmte_id:{}, report_id:{}".format(cmte_id, report_id)
            )
            cursor.execute(_sql, (activity_event_name, cmte_id, report_id))
            return int(cursor.fetchone()[0])
    except:
        raise


def check_if_activity_present(datum):
    report_id = datum.get("report_id")
    activity_name = datum.get("activity_event_name")
    activity_name = activity_name.replace(" ", "")
    fundraising_val = datum.get("fundraising")
    direct_cand_val = datum.get("direct_cand_support")

    if fundraising_val:
        event_type = "fundraising"
    elif direct_cand_val:
        event_type = "direct_cand_support"

    _sql = """
        select * from public.sched_h2
        where translate(lower(activity_event_name), ' ', '') = lower(%s)
        and fundraising = %s
        and direct_cand_support = %s
        and delete_ind is distinct from 'Y'
        """
    try:
        with connection.cursor() as cursor:
            cursor.execute(_sql, (activity_name, fundraising_val, direct_cand_val))
            event_list = cursor.fetchone()
            if event_list is not None:
                raise NoOPError(
                    "Same event activity already exist for report id:{} and event_type:{}".format(
                        report_id, event_type
                    )
                )
    except Exception as e:
        raise e


@api_view(["POST", "GET", "DELETE", "PUT"])
def schedH2(request):
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
                datum = schedH2_sql_dict(request.data)
                datum["report_id"] = report_id
                datum["cmte_id"] = cmte_id

                check_if_activity_present(datum)

                if "transaction_id" in request.data and check_null_value(
                        request.data.get("transaction_id")
                ):
                    datum["transaction_id"] = check_transaction_id(
                        request.data.get("transaction_id")
                    )
                    data = put_schedH2(datum)
                else:
                    # print(datum)
                    data = post_schedH2(datum)
                # Associating child transactions to parent and storing them to DB

                output = get_schedH2(data)
                return JsonResponse(output[0], status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response(str(e),
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
                datum = get_schedH2(data)
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
                    "The schedH2 API - GET is throwing an error: " + str(e),
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
                delete_schedH2(data)
                return Response(
                    "The Transaction ID: {} has been successfully deleted".format(
                        data.get("transaction_id")
                    ),
                    status=status.HTTP_201_CREATED,
                )
            except Exception as e:
                return Response(
                    "The schedH2 API - DELETE is throwing an error: " + str(e),
                    status=status.HTTP_400_BAD_REQUEST,
                )

        elif request.method == "PUT":
            try:
                datum = schedH2_sql_dict(request.data)
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

                data = put_schedH2(datum)
                return JsonResponse(data, status=status.HTTP_201_CREATED)
            except Exception as e:
                logger.debug(e)
                return Response(
                    "The schedH2 API - PUT is throwing an error: " + str(e),
                    status=status.HTTP_400_BAD_REQUEST,
                )
    except Exception as e:
        json_result = {'message': str(e)}
        return JsonResponse(json_result, status=status.HTTP_403_FORBIDDEN, safe=False)


"""
************************************************************************
SCHED_H3
Transfers from Nonfederal Accounts for Allocated Federal/Nonfederal Activity
***********************************************************************
"""


def check_mandatory_fields_SH3(data):
    """
    validate mandatory fields for sched_H3 item
    """
    try:
        errors = []
        for field in MANDATORY_FIELDS_SCHED_H3:
            if not (field in data and check_null_value(data.get(field))):
                errors.append(field)
        if errors:
            raise Exception(
                "The following mandatory fields are required in order to save data to schedH3 table: {}".format(
                    ",".join(errors)
                )
            )
    except:
        raise


def schedH3_sql_dict(data):
    """
    filter out valid fileds for sched_H3

    """
    valid_fields = [
        "cmte_id",
        "report_id",
        "transaction_type_identifier",
        "back_ref_transaction_id",
        "back_ref_sched_name",
        "account_name",
        "activity_event_type",
        "activity_event_name",
        "receipt_date",
        "total_amount_transferred",
        "transferred_amount",
        "memo_code",
        "memo_text",
    ]
    try:
        valid_data = {k: v for k, v in data.items() if k in valid_fields}
        valid_data["line_number"], valid_data[
            "transaction_type"
        ] = get_line_number_trans_type(data["transaction_type_identifier"])
        return valid_data
    except:
        raise Exception("invalid request data.")


def update_h3_total_amount(data):
    """
    update total amount for all transactions have the same parent_id
    """
    _sql = """
    UPDATE sched_h3 
    SET    total_amount_transferred = (
        SELECT Sum(transferred_amount) 
        FROM   sched_h3 
        WHERE 
              back_ref_transaction_id = %s) 
    WHERE  ( back_ref_transaction_id = %s 
          OR transaction_id = %s ) 
    """
    back_ref_transaction_id = data.get("back_ref_transaction_id")
    _v = [back_ref_transaction_id] * 3
    do_transaction(_sql, _v)


@update_F3X
@new_report_date
def put_schedH3(data):
    """
    update sched_H3 item
    here we are assuming entity_id are always referencing something already in our DB
    """
    # back_ref_transaction_id = data.get('back_ref_transaction_id')
    try:
        check_mandatory_fields_SH3(data)
        # check_transaction_id(data.get('transaction_id'))
        try:
            put_sql_schedH3(data)
            update_h3_total_amount(data)
        except Exception as e:
            raise Exception(
                "The put_sql_schedH3 function is throwing an error: " + str(e)
            )
        # return get_schedH3(data)
        return data
    except:
        raise


def put_sql_schedH3(data):
    """
    update a schedule_H3 item                    
            
    """
    _sql = """UPDATE public.sched_h3
              SET transaction_type_identifier = %s, 
                  back_ref_transaction_id = %s,
                  back_ref_sched_name = %s,
                  account_name = %s,
                  activity_event_type = %s,
                  activity_event_name = %s,
                  receipt_date = %s,
                  total_amount_transferred = %s,
                  transferred_amount = %s,
                  memo_code = %s,
                  memo_text = %s,
                  line_number = %s,
                  transaction_type = %s,
                  last_update_date = %s
              WHERE transaction_id = %s AND report_id = %s AND cmte_id = %s 
              AND delete_ind is distinct from 'Y';
        """
    _v = (
        data.get("transaction_type_identifier"),
        data.get("back_ref_transaction_id"),
        data.get("back_ref_sched_name"),
        data.get("account_name"),
        data.get("activity_event_type"),
        data.get("activity_event_name"),
        data.get("receipt_date"),
        data.get("total_amount_transferred"),
        data.get("transferred_amount"),
        data.get("memo_code"),
        data.get("memo_text"),
        data.get("line_number"),
        data.get("transaction_type"),
        datetime.datetime.now(),
        data.get("transaction_id"),
        data.get("report_id"),
        data.get("cmte_id"),
    )
    do_transaction(_sql, _v)


def validate_sh3_data(data):
    """
    validate sH3 json data
    """
    check_mandatory_fields_SH3(data)
    # TODO: temp_change
    if not data.get("total_amount_transferred"):
        data["total_amount_transferred"] = 0


@update_F3X
@new_report_date
def post_schedH3(data):
    """
    function for handling POST request for sH3, need to:
    1. generatye new transaction_id
    2. validate data
    3. save data to db
    """
    try:
        # check_mandatory_fields_SA(datum, MANDATORY_FIELDS_SCHED_A)
        data["transaction_id"] = get_next_transaction_id("SH3")
        # print(data)
        validate_sh3_data(data)
        try:
            post_sql_schedH3(data)
        except Exception as e:
            raise Exception(
                "The post_sql_schedH3 function is throwing an error: " + str(e)
            )
        logger.debug("data saved successfully.")
        return data
    except:
        raise


def post_sql_schedH3(data):
    try:
        _sql = """
        INSERT INTO public.sched_h3 (
            cmte_id,
            report_id,
            transaction_type_identifier,
            transaction_id,
            back_ref_transaction_id,
            back_ref_sched_name,
            account_name,
            activity_event_type,
            activity_event_name,
            receipt_date,
            total_amount_transferred,
            transferred_amount,
            memo_code,
            memo_text,
            line_number,
            transaction_type,
            create_date ,
            last_update_date
            )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s); 
        """
        _v = (
            data.get("cmte_id"),
            data.get("report_id"),
            data.get("transaction_type_identifier"),
            data.get("transaction_id"),
            data.get("back_ref_transaction_id"),
            data.get("back_ref_sched_name"),
            data.get("account_name"),
            data.get("activity_event_type"),
            data.get("activity_event_name"),
            data.get("receipt_date"),
            data.get("total_amount_transferred"),
            data.get("transferred_amount"),
            data.get("memo_code"),
            data.get("memo_text"),
            data.get("line_number"),
            data.get("transaction_type"),
            datetime.datetime.now(),
            datetime.datetime.now(),
        )
        with connection.cursor() as cursor:
            # Insert data into schedH3 table
            cursor.execute(_sql, _v)
    except Exception:
        raise


def get_schedH3(data):
    """
    load sched_H3 data based on cmte_id, report_id and transaction_id
    """
    try:
        cmte_id = data.get("cmte_id")
        report_id = data.get("report_id")
        if "transaction_id" in data:
            transaction_id = check_transaction_id(data.get("transaction_id"))
            forms_obj = get_list_schedH3(report_id, cmte_id, transaction_id)
            for _obj in forms_obj:
                child_list = get_child_schedH3(transaction_id, report_id, cmte_id)
                if child_list:
                    _obj["child"] = child_list
        else:
            forms_obj = get_list_all_schedH3(report_id, cmte_id)
            # print('---')
            # print(forms_obj)
            if forms_obj:
                for _obj in forms_obj:
                    transaction_id = _obj.get("transaction_id")
                    child_list = get_child_schedH3(transaction_id, report_id, cmte_id)
                    if child_list:
                        _obj["child"] = child_list
        return forms_obj
    except:
        raise


def get_child_schedH3(transaction_id, report_id, cmte_id):
    """
    load all child transaction for each parent H3
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
            account_name,
            activity_event_type,
            activity_event_name,
            receipt_date,
            total_amount_transferred,
            transferred_amount,
            memo_code,
            memo_text,
            line_number,
            transaction_type,
            delete_ind,
            create_date ,
            last_update_date
            FROM public.sched_h3
            WHERE report_id = %s 
            AND cmte_id = %s
            AND back_ref_transaction_id = %s
            AND delete_ind is distinct from 'Y') t
            """
            cursor.execute(_sql, (report_id, cmte_id, transaction_id))
            schedH3_list = cursor.fetchone()[0]
            # if schedH3_list is None:
            #     raise NoOPError('No sched_H3 transaction found for report_id {} and cmte_id: {}'.format(
            #         report_id, cmte_id))
            # merged_list = []
            # for dictH3 in schedH3_list:
            #     merged_list.append(dictH3)
        return schedH3_list
    except Exception:
        raise


def get_list_all_schedH3(report_id, cmte_id):
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
            account_name,
            activity_event_type,
            activity_event_name,
            receipt_date,
            total_amount_transferred,
            transferred_amount,
            memo_code,
            memo_text,
            line_number,
            transaction_type,
            delete_ind,
            create_date ,
            last_update_date
            FROM public.sched_h3
            WHERE report_id = %s AND cmte_id = %s
            AND delete_ind is distinct from 'Y') t
            """
            cursor.execute(_sql, (report_id, cmte_id))
            # print(_sql)
            # cursor.execute(_sql)
            return cursor.fetchone()[0]

        #     print(schedH3_list)
        #     if schedH3_list:
        #     # if not schedH3_list:
        #         raise NoOPError('No sched_H3 transaction found for report_id {} and cmte_id: {}'.format(
        #             report_id, cmte_id))
        #     merged_list = []
        #     for dictH3 in schedH3_list:
        #         merged_list.append(dictH3)
        # return merged_list
    except Exception:
        raise


def get_list_schedH3(report_id, cmte_id, transaction_id):
    try:
        with connection.cursor() as cursor:
            # GET single row from schedH3 table
            _sql = """SELECT json_agg(t) FROM ( SELECT
            cmte_id,
            report_id,
            transaction_type_identifier,
            transaction_id,
            back_ref_transaction_id,
            back_ref_sched_name,
            account_name,
            activity_event_type,
            activity_event_name,
            receipt_date,
            total_amount_transferred,
            transferred_amount,
            memo_code,
            memo_text,
            line_number,
            transaction_type,
            delete_ind,
            create_date ,
            last_update_date
            FROM public.sched_h3
            WHERE report_id = %s AND cmte_id = %s AND transaction_id = %s
            AND delete_ind is distinct from 'Y') t
            """
            cursor.execute(_sql, (report_id, cmte_id, transaction_id))
            schedH3_list = cursor.fetchone()[0]
            if schedH3_list is None:
                raise NoOPError(
                    "No sched_H3 transaction found for transaction_id {}".format(
                        transaction_id
                    )
                )
            if schedH3_list:
                for _rec in schedH3_list:
                    aggregate_dic = load_h3_aggregate_amount(
                            cmte_id, report_id, _rec.get("back_ref_transaction_id")
                        )
                    if _rec["activity_event_name"]:
                        _rec["aggregate_amount"] = aggregate_dic.get(
                            _rec["activity_event_name"], 0
                        )
                    else:
                        _rec["aggregate_amount"] = aggregate_dic.get(
                            _rec["activity_event_type"], 0
                        )
                        # pass
            merged_list = []
            for dictH3 in schedH3_list:
                merged_list.append(dictH3)
        return merged_list
    except Exception:
        raise


def delete_sql_schedH3(cmte_id, report_id, transaction_id):
    """
    do delete sql transaction
    """
    _sql = """UPDATE public.sched_h3
            SET delete_ind = 'Y' 
            WHERE transaction_id = %s AND report_id = %s AND cmte_id = %s
        """
    _v = (transaction_id, report_id, cmte_id)
    do_transaction(_sql, _v)


def delete_schedH3(data):
    """
    function for handling delete request for sh3
    """
    try:

        delete_sql_schedH3(
            data.get("cmte_id"), data.get("report_id"), data.get("transaction_id")
        )
    except Exception as e:
        raise


@api_view(["GET"])
def get_sched_h3_breakdown(request):
    """
    get h3 breakdown values for each event type and sum of all event types
    """
    _sql = """
    SELECT json_agg(t) FROM(
    SELECT activity_event_type, sum(transferred_amount) 
    FROM public.sched_h3 
    WHERE report_id = %s 
    AND cmte_id = %s
    AND back_ref_transaction_id is not null
    AND delete_ind is distinct from 'Y'
    GROUP BY activity_event_type) t
    """
    #     print(0)
    # except print(0):
    #     pass
    # union
    # SELECT 'total', sum(total_amount_transferred)
    # FROM public.sched_h3
    # WHERE report_id = %s
    # AND cmte_id = %s
    # AND back_ref_transaction_id is null
    # AND delete_ind is distinct from 'Y') t
    # """
    try:
        cmte_id = get_comittee_id(request.user.username)
        if not ("report_id" in request.query_params):
            raise Exception("Missing Input: Report_id is mandatory")
        # handling null,none value of report_id
        if not (check_null_value(request.query_params.get("report_id"))):
            report_id = "0"
        else:
            report_id = check_report_id(request.query_params.get("report_id"))
        with connection.cursor() as cursor:
            cursor.execute(_sql, [report_id, cmte_id])
            result = cursor.fetchone()[0]
            # print('...')
            # print(result)
            if result:
                _total = 0
                for _rec in result:
                    if _rec.get("sum"):
                        _total += float(_rec.get("sum"))
                total = {"activity_event_type": "total", "sum": _total}
                result.append(total)
            logger.debug("h3 breakdown:{}".format(result))
        return Response(result, status=status.HTTP_200_OK)
    except Exception as e:
        raise Exception("Error on fetching h3 break down")


def load_h3_aggregate_amount(cmte_id, report_id, back_ref_transaction_id):
    """
    query and caclcualte event_type or event_name based on aggregate amount 
    for current report
    """

    aggregate_dic = {}
    _sql = """
    SELECT json_agg(t) FROM(
            SELECT activity_event_name as event, 
                   SUM(transferred_amount) as sum
            FROM   public.sched_h3 
            WHERE  cmte_id = %s
                AND report_id = %s
                AND back_ref_transaction_id = %s
                AND delete_ind is distinct from 'Y'
            GROUP BY activity_event_name
    UNION
    SELECT activity_event_type as event,
                   SUM(transferred_amount) as sum
            FROM   public.sched_h3
            WHERE  cmte_id = %s
                AND report_id = %s
                AND back_ref_transaction_id = %s
                AND delete_ind is distinct from 'Y'
           GROUP BY activity_event_type
            ) t
    """
    # _sql = """
    # SELECT json_agg(t) FROM(
    #         SELECT activity_event_name as event,
    #                SUM(transferred_amount) as sum
    #         FROM   public.sched_h3
    #         WHERE  cmte_id = %s
    #             AND report_id = %s
    #         GROUP BY activity_event_name
    #         UNION
    #         SELECT activity_event_type as event,
    #                SUM(transferred_amount) as sum
    #         FROM   public.sched_h3
    #         WHERE  cmte_id = %s
    #             AND report_id = %s
    #         GROUP BY activity_event_type
    #         ) t
    # """.format(cmte_id, report_id, cmte_id, report_id)
    try:
        with connection.cursor() as cursor:
            cursor.execute(_sql, [cmte_id, report_id, back_ref_transaction_id,
                cmte_id, report_id, back_ref_transaction_id])
            # cursor.execute(_sql)
            records = cursor.fetchone()[0]
            if records:
                for _rec in records:
                    aggregate_dic[_rec["event"]] = _rec["sum"]
        return aggregate_dic
    except:
        raise


@api_view(["GET"])
def get_h3_account_names(request):
    """
    get existing h3 account names so people can choose one for use 
    """
    try:
        logger.debug("get_h3_account_names...")
        cmte_id = get_comittee_id(request.user.username)
        report_id = request.query_params.get("report_id")
        # aggregate_dic = load_h3_aggregate_amount(cmte_id, report_id)
        logger.debug("cmte_id:{}, report_id:{}".format(cmte_id, report_id))
        with connection.cursor() as cursor:
            # GET single row from schedA table
            _sql = """
            SELECT json_agg(t) FROM ( 
            SELECT distinct account_name
            FROM public.sched_h3
            WHERE report_id = %s AND cmte_id = %s
            AND back_ref_transaction_id is not null
            AND delete_ind is distinct from 'Y'
            ) t
            """
            cursor.execute(_sql, (report_id, cmte_id))
            # print(_sql)
            # cursor.execute(_sql)
            _sum = cursor.fetchone()[0]
            # if _sum:
            #     for _rec in _sum:
            #         if _rec['activity_event_name']:
            #             aggregate_dic = load_h3_aggregate_amount(cmte_id, report_id, _rec.get('back_ref_transaction_id'))
            #             _rec['aggregate_amount'] = aggregate_dic.get(_rec['activity_event_name'], 0)
            #         # elif _rec['activity_event_type']:
            #         #     _rec['aggregate_amount'] = aggregate_dic.get(_rec['activity_event_type'], 0)
            #         else:
            #             _rec['aggregate_amount'] = 0
            #             # pass
            return Response(_sum, status=status.HTTP_200_OK)
    except:
        raise


@api_view(["GET"])
def get_h3_summary(request):
    """
    get h3 summary for enabling summary page
    if a event_name is provided, will get the aggreaget amount based on event_name
    if no name provided, will get the aggregate amount based on event type
    1. load all child items only
    2. add aggregate amount
    3. report_id based.

    # TODO: what is gonna happen when people click edit button? 
    """
    try:
        logger.debug("get_h3_summary...")
#: Insert pagination functionality
        query_params = request.query_params
        page_num = get_int_value(query_params.get("page"))

        descending = query_params.get("descending")
        if not (
            "sortColumnName" in query_params
            and check_null_value(query_params.get("sortColumnName"))
        ):
            sortcolumn = "name"
        elif query_params.get("sortColumnName") == "default":
            sortcolumn = "name"
        else:
            sortcolumn = query_params.get("sortColumnName")
        itemsperpage =  get_int_value(query_params.get("itemsPerPage"))
        search_string = query_params.get("search")
        params = query_params.get("filters", {})
        keywords = params.get("keywords")
        if str(descending).lower() == "true":
            descending = "DESC"
        else:
            descending = "ASC"
        trans_query_string_count = ""
        row1=""
        totalcount=""

        #: Hardcode cmte value for now and remove after dev complete
        #cmte_id = "C00000935"
        cmte_id = get_comittee_id(request.user.username)

        report_id = request.query_params.get("report_id")
        # aggregate_dic = load_h3_aggregate_amount(cmte_id, report_id)
        logger.debug("cmte_id:{}, report_id:{}".format(cmte_id, report_id))
        with connection.cursor() as cursor:
            # GET single row from schedA table
            _sql = """
            SELECT json_agg(t) FROM ( 
                SELECT
            cmte_id,
            report_id,
            transaction_type_identifier,
            transaction_id,
            back_ref_transaction_id,
            back_ref_sched_name,
            account_name,
            activity_event_type,
            activity_event_name,
            receipt_date,
            total_amount_transferred,
            transferred_amount,
            memo_code,
            memo_text,
            delete_ind,
            create_date ,
            last_update_date
            FROM public.sched_h3
            WHERE (report_id = %s or report_id = 0) AND cmte_id = %s 
            AND back_ref_transaction_id is not null
            AND delete_ind is distinct from 'Y'
            ) t
            """
            cursor.execute(_sql, (report_id, cmte_id))
            # print(_sql)
            # cursor.execute(_sql)
            _sum = cursor.fetchone()[0]
            # print(cursor.query)
            if _sum:
                for _rec in _sum:
                    aggregate_dic = load_h3_aggregate_amount(
                            cmte_id, report_id, _rec.get("back_ref_transaction_id")
                        )
                    if _rec["activity_event_name"] not in [None, '']:
                        _rec["aggregate_amount"] = aggregate_dic.get(
                            _rec["activity_event_name"], 0
                        )
                    # elif _rec['activity_event_type']:
                    #     _rec['aggregate_amount'] = aggregate_dic.get(_rec['activity_event_type'], 0)
                    else:
                        _rec["aggregate_amount"] = aggregate_dic.get(
                            _rec["activity_event_type"], 0
                        )
                        # pass

            json_result = get_pagination_dataset(_sum, itemsperpage, page_num)
            return Response(json_result, status=status.HTTP_200_OK)
            #return Response(_sum, status=status.HTTP_200_OK)
    except:
        raise


@api_view(["GET"])
def get_h3_total_amount(request):
    """
    get h3 total_amount for editing purpose
    if a event_name is provided, will get the total amount based on event name
    if a event_type is provided, will get the total amount based on event type
    # TODO: this api need to be updated to calcuate a aggreaget amount
    """
    try:
        cmte_id = get_comittee_id(request.user.username)
        report_id = request.query_params.get("report_id")
        logger.debug("get_h3_total_amount with request:{}".format(request.query_params))
        if "activity_event_name" in request.query_params:
            event_name = request.query_params.get("activity_event_name")
            _sql = """
            SELECT json_agg(t) from(
            SELECT sum(transferred_amount) as aggregate_amount
            FROM   public.sched_h3 
            WHERE  cmte_id = %s
                AND report_id = %s
                    AND activity_event_name = %s
            ) t
            """
            with connection.cursor() as cursor:
                logger.debug("query with _sql:{}".format(_sql))
                # logger.debug('query with cmte_id:{}, report_id:{}'.format(cmte_id, report_id))
                cursor.execute(_sql, (cmte_id, report_id, event_name))
                json_res = cursor.fetchone()[0]
        else:
            event_type = request.query_params.get("activity_event_type")
            if not event_type:
                raise Exception("event name or event type is required for this api")
            _sql = """
            SELECT json_agg(t) from(
            SELECT sum(transferred_amount) as aggregate_amount
            FROM   public.sched_h3 
            WHERE  cmte_id = %s
            AND report_id = %s
                AND activity_event_type = %s
            ) t
            """
            with connection.cursor() as cursor:
                logger.debug("query with _sql:{}".format(_sql))
                # logger.debug('query with cmte_id:{}, report_id:{}'.format(cmte_id, report_id))
                cursor.execute(_sql, (cmte_id, report_id, event_type))
                json_res = cursor.fetchone()[0]

            # print(json_res)
        if not json_res:
            return Response({"total_amount_transferred": 0}, status=status.HTTP_200_OK)
        # calendar_year = check_calendar_year(request.query_params.get('calendar_year'))
        # start_dt = datetime.date(int(calendar_year), 1, 1)
        # end_dt = datetime.date(int(calendar_year), 12, 31)
        return Response(json_res[0], status=status.HTTP_200_OK)
    except:
        raise


@api_view(["GET"])
def get_h3_aggregate_amount(request):
    """
    get h3 aggregate_amount for editing purpose
    if a event_name is provided, will get the total amount based on event name
    if a event_type is provided, will get the total amount based on event type
    # TODO: this api need to be updated to calcuate a aggreaget amount
    """
    try:
        cmte_id = get_comittee_id(request.user.username)
        report_id = request.query_params.get("report_id")
        parent_id = request.query_params.get("parent_id")
        logger.debug("get_h3_total_amount with request:{}".format(request.query_params))
        if "activity_event_name" in request.query_params:
            event_name = request.query_params.get("activity_event_name")
            _sql = """
            SELECT json_agg(t) from(
            SELECT sum(transferred_amount) as aggregate_amount
            FROM   public.sched_h3 
            WHERE  cmte_id = %s
                AND report_id = %s
                    AND activity_event_name = %s
                    AND back_ref_transaction_id = %s
                    AND delete_ind is distinct from 'Y'
            ) t
            """
            with connection.cursor() as cursor:
                logger.debug("query with _sql:{}".format(_sql))
                # logger.debug('query with cmte_id:{}, report_id:{}'.format(cmte_id, report_id))
                cursor.execute(_sql, (cmte_id, report_id, event_name, parent_id))
                json_res = cursor.fetchone()[0]
        else:
            event_type = request.query_params.get("activity_event_type")
            if not event_type:
                raise Exception("event name or event type is required for this api")
            _sql = """
            SELECT json_agg(t) from(
            SELECT sum(transferred_amount) as aggregate_amount
            FROM   public.sched_h3 
            WHERE  cmte_id = %s
            AND report_id = %s
                AND activity_event_type = %s
            ) t
            """
            with connection.cursor() as cursor:
                logger.debug("query with _sql:{}".format(_sql))
                # logger.debug('query with cmte_id:{}, report_id:{}'.format(cmte_id, report_id))
                cursor.execute(_sql, (cmte_id, report_id, event_type))
                json_res = cursor.fetchone()[0]

            # print(json_res)
        if not json_res:
            return Response({"aggregate_amount": 0}, status=status.HTTP_200_OK)
        # calendar_year = check_calendar_year(request.query_params.get('calendar_year'))
        # start_dt = datetime.date(int(calendar_year), 1, 1)
        # end_dt = datetime.date(int(calendar_year), 12, 31)
        return Response(json_res[0], status=status.HTTP_200_OK)
    except:
        raise


@api_view(["POST", "GET", "DELETE", "PUT"])
def schedH3(request):
    try:
        is_read_only_or_filer_reports(request)

        if request.method == "POST":
            try:
                logger.debug("POST a h3 with data:{}".format(request.data))
                cmte_id = get_comittee_id(request.user.username)
                if not ("report_id" in request.data):
                    raise Exception("Missing Input: Report_id is mandatory")
                # handling null,none value of report_id
                if not (check_null_value(request.data.get("report_id"))):
                    report_id = "0"
                else:
                    report_id = check_report_id(request.data.get("report_id"))
                # end of handling
                datum = schedH3_sql_dict(request.data)
                datum["report_id"] = report_id
                datum["cmte_id"] = cmte_id

                # **********************************
                # TODO: disable transaction_id checking for h3 to fix FNE-2142 bug
                # if "transaction_id" in request.data and check_null_value(
                #     request.data.get("transaction_id")
                # ):
                #     datum["transaction_id"] = check_transaction_id(
                #         request.data.get("transaction_id")
                #     )
                #     data = put_schedH3(datum)
                #     if "child" in request.data:
                #         for _c in request.data["child"]:
                #             parent_data = data
                #             # _c.update(parent_data)
                #             _c["back_ref_transaction_id"] = parent_data["transaction_id"]
                #             _c = schedH3_sql_dict(_c)
                #             put_schedH3(_c)
                # else:
                # print(datum)
                # ************************************

                logger.debug("saving h3 with data {}".format(datum))
                data = post_schedH3(datum)
                logger.debug("parent data saved:{}".format(data))
                if "child" in request.data:
                    for _c in request.data["child"]:
                        child_data = data
                        child_data.update(_c)
                        child_data["back_ref_transaction_id"] = data["transaction_id"]
                        child_data = schedH3_sql_dict(child_data)
                        logger.debug(
                            "saving child transaction with data {}".format(child_data)
                        )
                        post_schedH3(child_data)
                        logger.debug("child transaction saved.")
                # Associating child transactions to parent and storing them to DB

                output = get_schedH3(data)
                return JsonResponse(output[0], status=status.HTTP_201_CREATED)

            except Exception as e:
                return Response(
                    "The schedH3 API - POST is throwing an exception: " + str(e),
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
                datum = get_schedH3(data)
                if datum:
                    return JsonResponse(datum, status=status.HTTP_200_OK, safe=False)
                else:
                    return JsonResponse([], status=status.HTTP_200_OK, safe=False)

            except NoOPError as e:
                logger.debug(e)
                forms_obj = []
                return JsonResponse(
                    forms_obj, status=status.HTTP_204_NO_CONTENT, safe=False
                )
            except Exception as e:
                logger.debug(e)
                return Response(
                    "The schedH3 API - GET is throwing an error: " + str(e),
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
                delete_schedH3(data)
                return Response(
                    "The Transaction ID: {} has been successfully deleted".format(
                        data.get("transaction_id")
                    ),
                    status=status.HTTP_201_CREATED,
                )
            except Exception as e:
                return Response(
                    "The schedH3 API - DELETE is throwing an error: " + str(e),
                    status=status.HTTP_400_BAD_REQUEST,
                )

        elif request.method == "PUT":
            try:
                datum = schedH3_sql_dict(request.data)
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

                # if 'entity_id' in request.data and check_null_value(request.data.get('entity_id')):
                #     datum['entity_id'] = request.data.get('entity_id')
                # if request.data.get('transaction_type') in CHILD_SCHED_B_TYPES:
                #     data = put_schedB(datum)
                #     output = get_schedB(data)
                # else:
                data = put_schedH3(datum)
                output = get_schedH3(data)
                return JsonResponse(output[0], status=status.HTTP_201_CREATED, safe=False)
            except Exception as e:
                logger.debug(e)
                return Response(
                    "The schedH3 API - PUT is throwing an error: " + str(e),
                    status=status.HTTP_400_BAD_REQUEST,
                )
    except Exception as e:
        json_result = {'message': str(e)}
        return JsonResponse(json_result, status=status.HTTP_403_FORBIDDEN, safe=False)


"""
************************************************* CRUD API FOR SCHEDULE_H4 ********************************************************************************

Disbursements for Allocated Federal/Nonfederal Activity
some check points:
1. when h4 activity is submitted, make sure an h1 or h2 is there to calcualte 
   the fed and non-fed amount
2. when a memo transaction is submitted, need to verify the parent transaction exist

"""
SCHED_H4_CHILD_TRANSACTIONS = [
    "ALLOC_EXP_CC_PAY_MEMO",
    "ALLOC_EXP_STAF_REIM_MEMO",
    "ALLOC_EXP_PMT_TO_PROL_MEMO",
]


def check_mandatory_fields_SH4(data):
    """
    validate mandatory fields for sched_H4 item
    """
    try:
        errors = []
        for field in MANDATORY_FIELDS_SCHED_H4:
            if not (field in data and check_null_value(data.get(field))):
                errors.append(field)
        if errors:
            raise Exception(
                "The following mandatory fields are required in order to save data to schedH4 table: {}".format(
                    ",".join(errors)
                )
            )
    except:
        raise


def schedH4_sql_dict(data):
    """
    filter out valid fileds for sched_H4

    """
    logger.debug("request data:{}".format(data))
    valid_fields = [
        "transaction_type_identifier",
        "back_ref_transaction_id",
        "back_ref_sched_name",
        "payee_entity_id",
        "activity_event_identifier",
        "expenditure_date",
        "fed_share_amount",
        "non_fed_share_amount",
        "total_amount",
        "activity_event_amount_ytd",
        "purpose",
        "category_code",
        "activity_event_type",
        "memo_code",
        "memo_text",
        "aggregation_ind",
        # entity_data
        "entity_id",
        "entity_type",
        "entity_name",
        "first_name",
        "last_name",
        "middle_name",
        "preffix",
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
        # return {k: v for k, v in data.items() if k in valid_fields}
        valid_data = {k: v for k, v in data.items() if k in valid_fields}
        line_num, tran_tp = get_line_number_trans_type(
            data["transaction_type_identifier"]
        )

        valid_data["line_number"] = line_num
        valid_data["transaction_type"] = tran_tp
        # TODO: this is a temp code change, we need to update h4,h6
        # to unify the field names
        if "expenditure_purpose" in data:
            valid_data["purpose"] = data.get("expenditure_purpose", "")
        return valid_data
    except:
        raise Exception("invalid request data.")


def get_existing_h4_total(cmte_id, transaction_id):
    """
    fetch existing close balance in the db for current transaction
    """
    _sql = """
    select total_amount
    from public.sched_h4
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
def put_schedH4(data):
    """
    update sched_H4 item
    
    """
    try:
        check_mandatory_fields_SH4(data)
        if "entity_id" in data:
            get_data = {
                "cmte_id": data.get("cmte_id"),
                "entity_id": data.get("entity_id"),
            }

            # need this update for FEC entity
            if get_data["entity_id"].startswith("FEC"):
                get_data["cmte_id"] = "C00000000"

            prev_entity_list = get_entities(get_data)
            entity_data = put_entities(data)
            roll_back = True
        else:
            entity_data = post_entities(data)
            roll_back = False

        # continue to save transaction
        entity_id = entity_data.get("entity_id")
        data["entity_id"] = entity_id
        data["payee_entity_id"] = entity_id
        # check_transaction_id(data.get('transaction_id'))

        existing_total = get_existing_h4_total(
            data.get("cmte_id"), data.get("transaction_id")
        )
        try:
            put_sql_schedH4(data)
            # update ytd aggregation if not memo transaction
            if not data.get("transaction_type_identifier").endswith("_MEMO"):
                update_activity_event_amount_ytd(data)

            # if debt payment, update parent sched_d
            if data.get("transaction_type_identifier") == "ALLOC_EXP_DEBT":
                if float(existing_total) != float(data.get("total_amount")):
                    update_sched_d_parent(
                        data.get("cmte_id"),
                        data.get("back_ref_transaction_id"),
                        data.get("total_amount"),
                        existing_total,
                    )
        except Exception as e:
            if roll_back:
                entity_data = put_entities(prev_entity_list[0])
            else:
                get_data = {"cmte_id": data.get("cmte_id"), "entity_id": entity_id}
                remove_entities(get_data)
            raise Exception(
                "The put_sql_schedH4 function is throwing an error: " + str(e)
            )
        return data
    except:
        raise


def put_sql_schedH4(data):
    """
    update a schedule_H4 item                    
    """
    _sql = """UPDATE public.sched_h4
              SET transaction_type_identifier= %s, 
                  back_ref_transaction_id = %s,
                  back_ref_sched_name = %s,
                  payee_entity_id = %s,
                  activity_event_identifier = %s,
                  expenditure_date = %s,
                  fed_share_amount = %s,
                  non_fed_share_amount = %s,
                  total_amount = %s,
                  activity_event_amount_ytd = %s,
                  purpose = %s,
                  category_code = %s,
                  activity_event_type = %s,
                  memo_code = %s,
                  memo_text = %s,
                  line_number = %s, 
                  transaction_type = %s,
                  aggregation_ind = %s,
                  last_update_date= %s
              WHERE transaction_id = %s AND report_id = %s AND cmte_id = %s 
              AND delete_ind is distinct from 'Y'
        """
    _v = (
        data.get("transaction_type_identifier"),
        data.get("back_ref_transaction_id"),
        data.get("back_ref_sched_name"),
        data.get("payee_entity_id"),
        data.get("activity_event_identifier"),
        data.get("expenditure_date"),
        data.get("fed_share_amount"),
        data.get("non_fed_share_amount"),
        data.get("total_amount"),
        data.get("activity_event_amount_ytd"),
        data.get("purpose"),
        data.get("category_code"),
        data.get("activity_event_type"),
        data.get("memo_code"),
        data.get("memo_text"),
        data.get("line_number"),
        data.get("transaction_type"),
        data.get("aggregation_ind"),
        datetime.datetime.now(),
        data.get("transaction_id"),
        data.get("report_id"),
        data.get("cmte_id"),
    )
    do_transaction(_sql, _v)


def validate_parent_transaction_exist(data):
    """
    validate parent transaction exsit if saving a child transaction
    """
    # if data.get("transaction_type_identifier") in SCHED_H4_CHILD_TRANSACTIONS:
    if not data.get("back_ref_transaction_id"):
        raise Exception("Error: parent transaction id missing.")
    elif not transaction_exists(data.get("back_ref_transaction_id"), "sched_h4"):
        raise Exception("Error: parent transaction not found.")
    else:
        pass


def validate_fed_nonfed_share(data):
    # remove ',' in the number if number is passed in as string
    for _rec in ["fed_share_amount", "non_fed_share_amount", "total_amount"]:
        if "," in str(data.get(_rec)):
            data[_rec] = data[_rec].replace(",", "")
    if float(data.get("fed_share_amount")) + float(
            data.get("non_fed_share_amount")
    ) != float(data.get("total_amount")):
        raise Exception(
            "Error: fed_amount and non_fed_amount should sum to total amount."
        )


def validate_sh4_data(data):
    """
    validate sH4 json data
    """
    check_mandatory_fields_SH4(data)
    validate_fed_nonfed_share(data)
    if data.get("transaction_type_identifier") in SCHED_H4_CHILD_TRANSACTIONS:
        validate_parent_transaction_exist(data)


def list_all_transactions_event_type(start_dt, end_dt, activity_event_type, cmte_id):
    """
    load all transactions with the specified activity event type
    need to check
    """
    logger.debug(
        "load ttransactionsransactions with activity_event_type:{}".format(
            activity_event_type
        )
    )
    # logger.debug('load ttransactionsransactions with start:{}, end {}'.format(start_dt, end_dt))
    # logger.debug('load ttransactionsransactions with cmte-id:{}'.format(cmte_id))
    _sql = """
            SELECT t1.total_amount, 
                t1.transaction_id,
                t1.aggregation_ind
            FROM public.sched_h4 t1 
            WHERE activity_event_type = %s 
            AND cmte_id = %s
            AND expenditure_date >= %s
            AND expenditure_date <= %s 
            AND back_ref_transaction_id is null
            AND delete_ind is distinct FROM 'Y' 
            ORDER BY expenditure_date ASC, create_date ASC
    """
    # .format(activity_event_type, cmte_id, start_dt, end_dt)
    logger.debug(_sql)
    try:
        with connection.cursor() as cursor:
            cursor.execute(_sql, (activity_event_type, cmte_id, start_dt, end_dt))
            # , [
            #         activity_event_type,
            #         cmte_id,
            #         start_dt,
            #         end_dt,
            #     ])
            transactions_list = cursor.fetchall()
            logger.debug("transaction fetched:{}".format(transactions_list))
        return transactions_list
    except Exception as e:
        raise Exception(
            "The list_all_transactions_event_type function is throwing an error: "
            + str(e)
        )


def list_all_transactions_event_identifier(
        start_dt, end_dt, activity_event_identifier, cmte_id
):
    """
    load all transactions with the specified activity event type
    need to check
    """
    logger.debug(
        "load ttransactionsransactions with activity_event_identifier:{}".format(
            activity_event_identifier
        )
    )
    # logger.debug('load ttransactionsransactions with start:{}, end {}'.format(start_dt, end_dt))
    # logger.debug('load ttransactionsransactions with cmte-id:{}'.format(cmte_id))
    _sql = """
            SELECT t1.total_amount, 
                t1.transaction_id,
                t1.aggregation_ind
            FROM public.sched_h4 t1 
            WHERE activity_event_identifier = %s 
            AND cmte_id = %s
            AND expenditure_date >= %s
            AND expenditure_date <= %s 
            AND back_ref_transaction_id is null
            AND delete_ind is distinct FROM 'Y' 
            ORDER BY expenditure_date ASC, create_date ASC
    """
    # .format(activity_event_type, cmte_id, start_dt, end_dt)
    logger.debug(_sql)
    try:
        with connection.cursor() as cursor:
            cursor.execute(_sql, (activity_event_identifier, cmte_id, start_dt, end_dt))
            # , [
            #         activity_event_type,
            #         cmte_id,
            #         start_dt,
            #         end_dt,
            #     ])
            transactions_list = cursor.fetchall()
            logger.debug("transaction fetched:{}".format(transactions_list))
        return transactions_list
    except Exception as e:
        raise Exception(
            "The list_all_transactions_event_identifier function is throwing an error: "
            + str(e)
        )


def update_transaction_ytd_amount(cmte_id, transaction_id, aggregate_amount):
    """
    update h4 ytd amount
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """ UPDATE public.sched_h4
                    SET activity_event_amount_ytd = %s 
                    WHERE transaction_id = %s AND cmte_id = %s AND delete_ind is distinct from 'Y'
                    """,
                [aggregate_amount, transaction_id, cmte_id],
            )
            if cursor.rowcount == 0:
                raise Exception(
                    "Error: The Transaction ID: {} does not exist in schedH4 table".format(
                        transaction_id
                    )
                )
    except Exception:
        raise


def update_activity_event_amount_ytd(data):
    """
    aggregate and update 'activity_event_amount_ytd' for all h4 transactions
    if event_identifier is provided, will do event-based aggregation;
    else will do event_type-based aggregation
    """
    try:

        logger.debug("updating ytd amount:")
        # make sure transaction list comes back sorted by contribution_date ASC
        expenditure_dt = date_format(data.get("expenditure_date"))
        aggregate_start_date = datetime.date(expenditure_dt.year, 1, 1)
        aggregate_end_date = datetime.date(expenditure_dt.year, 12, 31)
        if data.get("activity_event_identifier"):
            transactions_list = list_all_transactions_event_identifier(
                aggregate_start_date,
                aggregate_end_date,
                data.get("activity_event_identifier"),
                data.get("cmte_id"),
            )
        else:
            transactions_list = list_all_transactions_event_type(
                aggregate_start_date,
                aggregate_end_date,
                data.get("activity_event_type"),
                data.get("cmte_id"),
            )
        aggregate_amount = 0
        for transaction in transactions_list:
            if transaction[2] != "N":
                aggregate_amount += transaction[0]
            transaction_id = transaction[1]
            update_transaction_ytd_amount(
                data.get("cmte_id"), transaction_id, aggregate_amount
            )

    except Exception as e:
        raise Exception(
            "The update_activity_event_amount_ytd function is throwing an error: "
            + str(e)
        )


@update_F3X
@new_report_date
def post_schedH4(data):
    """
    function for handling POST request for sH4, need to:
    1. generatye new transaction_id
    2. validate data
    3. save data to db
    """
    try:
        if "entity_id" in data:
            get_data = {
                "cmte_id": data.get("cmte_id"),
                "entity_id": data.get("entity_id"),
            }

            # need this update for FEC entity
            if get_data["entity_id"].startswith("FEC"):
                get_data["cmte_id"] = "C00000000"

            prev_entity_list = get_entities(get_data)
            entity_data = put_entities(data)
            roll_back = True
        else:
            entity_data = post_entities(data)
            roll_back = False

        # continue to save transaction
        entity_id = entity_data.get("entity_id")
        data["entity_id"] = entity_id
        data["payee_entity_id"] = entity_id
        # check_mandatory_fields_SA(datum, MANDATORY_FIELDS_SCHED_H4)
        data["transaction_id"] = get_next_transaction_id("SH4")
        logger.debug("saving a new h4 transaction with data:{}".format(data))
        validate_sh4_data(data)
        try:
            post_sql_schedH4(data)
            # update ytd aggregation if not memo transaction
            # if not data.get("transaction_type_identifier").endswith("_MEMO"):
            logger.info("update ytd amount...")
            update_activity_event_amount_ytd(data)

            # sched_d debt payment, need to update parent
            if data.get("transaction_type_identifier") == "ALLOC_EXP_DEBT":
                update_sched_d_parent(
                    data.get("cmte_id"),
                    data.get("back_ref_transaction_id"),
                    data.get("total_amount"),
                )
        except Exception as e:
            if roll_back:
                entity_data = put_entities(prev_entity_list[0])
            else:
                get_data = {"cmte_id": data.get("cmte_id"), "entity_id": entity_id}
                remove_entities(get_data)
            raise Exception(
                "The post_sql_schedH4 function is throwing an error: " + str(e)
            )
        return data
    except:
        raise


def post_sql_schedH4(data):
    try:
        _sql = """
        INSERT INTO public.sched_h4 (
            cmte_id,
            report_id,
            transaction_type_identifier,
            transaction_id,
            back_ref_transaction_id,
            back_ref_sched_name,
            payee_entity_id,
            activity_event_identifier,
            expenditure_date,
            fed_share_amount,
            non_fed_share_amount,
            total_amount,
            activity_event_amount_ytd,
            purpose,
            category_code,
            activity_event_type,
            memo_code,
            memo_text,
            line_number,
            transaction_type,
            aggregation_ind,
            create_date
            )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s); 
        """
        _v = (
            data.get("cmte_id"),
            data.get("report_id"),
            data.get("transaction_type_identifier"),
            data.get("transaction_id"),
            data.get("back_ref_transaction_id"),
            data.get("back_ref_sched_name"),
            data.get("payee_entity_id"),
            data.get("activity_event_identifier"),
            data.get("expenditure_date"),
            data.get("fed_share_amount"),
            data.get("non_fed_share_amount"),
            data.get("total_amount"),
            data.get("activity_event_amount_ytd"),
            data.get("purpose"),
            data.get("category_code"),
            data.get("activity_event_type"),
            data.get("memo_code"),
            data.get("memo_text"),
            data.get("line_number"),
            data.get("transaction_type"),
            data.get("aggregation_ind"),
            datetime.datetime.now(),
        )
        with connection.cursor() as cursor:
            # Insert data into schedH4 table
            cursor.execute(_sql, _v)
    except Exception:
        raise


def get_schedH4(data):
    """
    load sched_H4 data based on cmte_id, report_id and transaction_id
    """
    try:
        cmte_id = data.get("cmte_id")
        report_id = data.get("report_id")
        if "transaction_id" in data:
            transaction_id = check_transaction_id(data.get("transaction_id"))
            forms_obj = get_list_schedH4(report_id, cmte_id, transaction_id)
        else:
            forms_obj = get_list_all_schedH4(report_id, cmte_id)

        # TODO: temp change, need to reove this code when h4, h6 schedma updated
        for obj in forms_obj:
            obj["expenditure_purpose"] = obj.get("purpose", "")
            obj["api_call"] = '/sh4/schedH4'
            child_data = get_sched_h4_child_transactions(
                obj.get("report_id"), obj.get("cmte_id"), obj.get("transaction_id")
            )
            if child_data:
                obj["child"] = child_data

        return forms_obj
    except:
        raise


def get_list_all_schedH4(report_id, cmte_id):
    try:
        with connection.cursor() as cursor:
            # GET single row from schedH4 table
            _sql = """SELECT json_agg(t) FROM ( SELECT
            cmte_id,
            report_id,
            transaction_type_identifier,
            transaction_id,
            back_ref_transaction_id,
            back_ref_sched_name,
            payee_entity_id,
            activity_event_identifier,
            expenditure_date,
            fed_share_amount,
            non_fed_share_amount,
            total_amount,
            activity_event_amount_ytd,
            purpose,
            category_code,
            activity_event_type,
            memo_code,
            memo_text,
            line_number,
            transaction_type,
            aggregation_ind,
            create_date,
            last_update_date
            FROM public.sched_h4
            WHERE report_id = %s AND cmte_id = %s
            AND delete_ind is distinct from 'Y') t
            """
            cursor.execute(_sql, (report_id, cmte_id))
            tran_list = cursor.fetchone()[0]
            if tran_list is None:
                raise NoOPError(
                    "No sched_H4 transaction found for report_id {} and cmte_id: {}".format(
                        report_id, cmte_id
                    )
                )
            merged_list = []
            for tran in tran_list:
                entity_id = tran.get("payee_entity_id")
                q_data = {"entity_id": entity_id, "cmte_id": cmte_id}
                dictEntity = get_entities(q_data)[0]
                merged_list.append({**tran, **dictEntity})
                # merged_list.append(dictH4)
        return merged_list
    except Exception:
        raise


def get_list_schedH4(report_id, cmte_id, transaction_id):
    try:
        with connection.cursor() as cursor:
            # GET single row from schedH4 table
            _sql = """SELECT json_agg(t) FROM ( SELECT
            cmte_id,
            report_id,
            transaction_type_identifier,
            transaction_id,
            back_ref_transaction_id,
            back_ref_sched_name,
            payee_entity_id,
            activity_event_identifier,
            expenditure_date,
            fed_share_amount,
            non_fed_share_amount,
            total_amount,
            activity_event_amount_ytd,
            purpose,
            category_code,
            activity_event_type,
            memo_code,
            memo_text,
            line_number,
            transaction_type,
            aggregation_ind,
            create_date,
            last_update_date
            FROM public.sched_h4
            WHERE report_id = %s AND cmte_id = %s AND transaction_id = %s
            AND delete_ind is distinct from 'Y') t
            """
            cursor.execute(_sql, (report_id, cmte_id, transaction_id))
            tran_list = cursor.fetchone()[0]
            if not tran_list:
                raise NoOPError(
                    "No sched_H4 transaction found for transaction_id {}".format(
                        transaction_id
                    )
                )
            merged_list = []
            for tran in tran_list:
                entity_id = tran.get("payee_entity_id")
                q_data = {"entity_id": entity_id, "cmte_id": cmte_id}
                dictEntity = get_entities(q_data)[0]
                merged_list.append({**tran, **dictEntity})
        return merged_list
    except Exception:
        raise


def delete_sql_schedH4(cmte_id, report_id, transaction_id):
    """
    do delete sql transaction
    """
    _sql = """UPDATE public.sched_h4
            SET delete_ind = 'Y' 
            WHERE transaction_id = %s AND report_id = %s AND cmte_id = %s
        """
    _v = (transaction_id, report_id, cmte_id)
    do_transaction(_sql, _v)


def delete_schedH4(data):
    """
    function for handling delete request for sh4
    """
    try:

        delete_sql_schedH4(
            data.get("cmte_id"), data.get("report_id"), data.get("transaction_id")
        )
    except Exception as e:
        raise


@api_view(["POST", "GET", "DELETE", "PUT"])
def schedH4(request):
    #: Get the request parameters and set for Pagination
    query_params = request.query_params
    page_num = get_int_value(query_params.get("page"))

    descending = query_params.get("descending")
    if not (
        "sortColumnName" in query_params
        and check_null_value(query_params.get("sortColumnName"))
    ):
        sortcolumn = "name"
    elif query_params.get("sortColumnName") == "default":
        sortcolumn = "name"
    else:
        sortcolumn = query_params.get("sortColumnName")
    itemsperpage =  get_int_value(query_params.get("itemsPerPage"))
    search_string = query_params.get("search")
    params = query_params.get("filters", {})
    keywords = params.get("keywords")
    if str(descending).lower() == "true":
        descending = "DESC"
    else:
        descending = "ASC"
    trans_query_string_count = ""

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
                datum = schedH4_sql_dict(request.data)
                datum["report_id"] = report_id
                datum["cmte_id"] = cmte_id
                if "transaction_id" in request.data and check_null_value(
                    request.data.get("transaction_id")
                ):
                    try:
                        datum["transaction_id"] = check_transaction_id(
                            request.data.get("transaction_id")
                        )
                        data = put_schedH4(datum)
                    except:
                        datum["transaction_id"] = None
                        data = post_schedH4(datum)
                else:
                    # print(datum)
                    data = post_schedH4(datum)
                # Associating child transactions to parent and storing them to DB

                output = get_schedH4(data)
                return JsonResponse(output[0], status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response(
                    "The schedH4 API - POST is throwing an exception: " + str(e),
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
                datum = get_schedH4(data)
                return JsonResponse(datum, status=status.HTTP_200_OK, safe=False)
            except NoOPError as e:
                logger.debug(e)
                #: updated the return status to 200 with null object for testing
                forms_obj = {
                    "items": "",
                    "totalItems": "",
                    "itemsPerPage": "",
                    "pageNumber": "",
                    "totalPages": "",
                }
                return JsonResponse(
                forms_obj, status=status.HTTP_200_OK, safe=False
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
                delete_schedH4(data)
                return Response(
                    "The Transaction ID: {} has been successfully deleted".format(
                        data.get("transaction_id")
                    ),
                    status=status.HTTP_201_CREATED,
                )
            except Exception as e:
                return Response(
                    "The schedH4 API - DELETE is throwing an error: " + str(e),
                    status=status.HTTP_400_BAD_REQUEST,
                )

        elif request.method == "PUT":
            try:
                datum = schedH4_sql_dict(request.data)
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

                # if 'entity_id' in request.data and check_null_value(request.data.get('entity_id')):
                #     datum['entity_id'] = request.data.get('entity_id')
                # if request.data.get('transaction_type') in CHILD_SCHED_B_TYPES:
                #     data = put_schedB(datum)
                #     output = get_schedB(data)
                # else:
                data = put_schedH4(datum)
                output = get_schedH4(data)[0]
                # output = get_schedA(data)
                return JsonResponse(output, status=status.HTTP_201_CREATED)
            except Exception as e:
                logger.debug(e)
                return Response(
                    "The schedH4 API - PUT is throwing an error: " + str(e),
                    status=status.HTTP_400_BAD_REQUEST,
                )

    except Exception as e:
        json_result = {'message': str(e)}
        return JsonResponse(json_result, status=status.HTTP_403_FORBIDDEN, safe=False)


"""

************************************************** CRUD API FOR SCHEDULE_H5 ***********************************************************************************

"""


def check_mandatory_fields_SH5(data):
    """
    validate mandatory fields for sched_H5 item
    """
    try:
        errors = []
        for field in MANDATORY_FIELDS_SCHED_H5:
            if not (field in data and check_null_value(data.get(field))):
                errors.append(field)
        if errors:
            raise Exception(
                "The following mandatory fields are required in order to save data to schedH5 table: {}".format(
                    ",".join(errors)
                )
            )
    except:
        raise


def schedH5_sql_dict(data):
    """
    filter out valid fileds for sched_H5

    """
    valid_fields = [
        "transaction_type_identifier",
        "account_name",
        "receipt_date",
        "total_amount_transferred",
        "voter_registration_amount",
        "voter_id_amount",
        "gotv_amount",
        "generic_campaign_amount",
        "back_ref_transaction_id",
        "memo_code",
        "memo_text",
    ]
    try:
        valid_data = {k: v for k, v in data.items() if k in valid_fields}
        valid_data["line_number"], valid_data[
            "transaction_type"
        ] = get_line_number_trans_type(data["transaction_type_identifier"])
        return valid_data
    except:
        raise Exception("invalid request data.")


def update_h5_total_amount(data):
    """
    update total amount for all transactions have the same parent_id
    """

    _sql = """
    UPDATE sched_h5 
    SET    total_amount_transferred = (
        SELECT Sum(coalesce(
                voter_registration_amount,
                voter_id_amount,
                gotv_amount,
                generic_campaign_amount)) 
        FROM   sched_h5 
        WHERE 
              back_ref_transaction_id = %s) 
    WHERE  ( back_ref_transaction_id = %s 
          OR transaction_id = %s ) 
    """
    back_ref_transaction_id = data.get("back_ref_transaction_id")
    _v = [back_ref_transaction_id] * 3
    if back_ref_transaction_id:
        do_transaction(_sql, _v)


@update_F3X
@new_report_date
def put_schedH5(data):
    """
    update sched_H5 item
    
    """
    try:
        check_mandatory_fields_SH5(data)
        # check_transaction_id(data.get('transaction_id'))
        try:
            put_sql_schedH5(data)
            logger.debug(
                "update total amount after H5 updates saved with data {}".format(data)
            )
            update_h5_total_amount(data)
        except Exception as e:
            raise Exception(
                "The put_sql_schedH5 function is throwing an error: " + str(e)
            )
        return get_list_schedH5(
            data.get("report_id"), data.get("cmte_id"), data.get("transaction_id")
        )[0]
    except:
        raise


def put_sql_schedH5(data):
    """
    update a schedule_H5 item                    
            
    """
    _sql = """UPDATE public.sched_h5
              SET transaction_type_identifier= %s, 
                  account_name= %s,
                  receipt_date= %s,
                  total_amount_transferred= %s,
                  voter_registration_amount= %s,
                  voter_id_amount= %s,
                  gotv_amount= %s,
                  generic_campaign_amount= %s,
                  memo_code= %s,
                  memo_text = %s,
                  line_number = %s,
                  transaction_type = %s,
                  back_ref_transaction_id = %s,
                  last_update_date= %s
              WHERE transaction_id = %s AND report_id = %s AND cmte_id = %s 
              AND delete_ind is distinct from 'Y';
        """
    _v = (
        data.get("transaction_type_identifier"),
        data.get("account_name"),
        data.get("receipt_date"),
        data.get("total_amount_transferred"),
        data.get("voter_registration_amount"),
        data.get("voter_id_amount"),
        data.get("gotv_amount"),
        data.get("generic_campaign_amount"),
        data.get("memo_code"),
        data.get("memo_text"),
        data.get("line_number"),
        data.get("transaction_type"),
        data.get("back_ref_transaction_id"),
        datetime.datetime.now(),
        data.get("transaction_id"),
        data.get("report_id"),
        data.get("cmte_id"),
    )
    do_transaction(_sql, _v)


def validate_sh5_data(data):
    """
    validate sH5 json data
    """
    check_mandatory_fields_SH5(data)


@update_F3X
@new_report_date
def post_schedH5(data):
    """
    function for handling POST request for sH5, need to:
    1. generatye new transaction_id
    2. validate data
    3. save data to db
    """
    try:
        # check_mandatory_fields_SH5(datum, MANDATORY_FIELDS_SCHED_H5)
        data["transaction_id"] = get_next_transaction_id("SH5")
        # print(data)
        validate_sh5_data(data)
        try:
            post_sql_schedH5(data)
        except Exception as e:
            raise Exception(
                "The post_sql_schedH5 function is throwing an error: " + str(e)
            )
        return data
    except:
        raise


def post_sql_schedH5(data):
    try:
        _sql = """
        INSERT INTO public.sched_h5 (
            cmte_id,
            report_id,
            transaction_type_identifier ,
            transaction_id,
            account_name,
            receipt_date,
            total_amount_transferred,
            voter_registration_amount,
            voter_id_amount,
            gotv_amount,
            generic_campaign_amount,
            memo_code,
            memo_text,
            line_number,
            transaction_type,
            back_ref_transaction_id,
            create_date,
            last_update_date
            )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s); 
        """
        _v = (
            data.get("cmte_id"),
            data.get("report_id"),
            data.get("transaction_type_identifier"),
            data.get("transaction_id"),
            data.get("account_name"),
            data.get("receipt_date"),
            data.get("total_amount_transferred"),
            data.get("voter_registration_amount"),
            data.get("voter_id_amount"),
            data.get("gotv_amount"),
            data.get("generic_campaign_amount"),
            data.get("memo_code"),
            data.get("memo_text"),
            data.get("line_number"),
            data.get("transaction_type"),
            data.get("back_ref_transaction_id"),
            datetime.datetime.now(),
            datetime.datetime.now(),
        )
        with connection.cursor() as cursor:
            # Insert data into schedH5 table
            cursor.execute(_sql, _v)
    except Exception:
        raise


def get_schedH5(data):
    """
    load sched_H5 data based on cmte_id, report_id and/or transaction_id
    all child transactions will also be loaded
    """
    try:
        cmte_id = data.get("cmte_id")
        report_id = data.get("report_id")
        if "transaction_id" in data:
            transaction_id = check_transaction_id(data.get("transaction_id"))
            forms_obj = get_list_schedH5(report_id, cmte_id, transaction_id)
            if forms_obj:
                for _obj in forms_obj:
                    child_list = get_child_schedH5(transaction_id, report_id, cmte_id)
                    if child_list:
                        _obj["child"] = child_list
        else:
            forms_obj = get_list_all_schedH5(report_id, cmte_id)
            if forms_obj:
                for _obj in forms_obj:
                    transaction_id = _obj.get("transaction_id")
                    child_list = get_child_schedH5(transaction_id, report_id, cmte_id)
                    if child_list:
                        _obj["child"] = child_list
        return forms_obj
    except:
        raise


def get_child_schedH5(transaction_id, report_id, cmte_id):
    """
    load all child transaction for each parent H5
    """
    try:
        with connection.cursor() as cursor:
            # GET single row from schedA table
            _sql = """SELECT json_agg(t) FROM ( SELECT
            cmte_id,
            report_id,
            transaction_type_identifier ,
            transaction_id,
            account_name,
            receipt_date,
            total_amount_transferred,
            voter_registration_amount,
            voter_id_amount,
            gotv_amount,
            generic_campaign_amount,
            memo_code,
            memo_text,
            line_number,
            transaction_type,
            back_ref_transaction_id,
            create_date,
            last_update_date
            FROM public.sched_h5
            WHERE report_id = %s 
            AND cmte_id = %s
            AND back_ref_transaction_id = %s
            AND delete_ind is distinct from 'Y') t
            """
            cursor.execute(_sql, (report_id, cmte_id, transaction_id))
            schedH5_list = cursor.fetchone()[0]
        return schedH5_list
    except Exception:
        raise


def get_list_all_schedH5(report_id, cmte_id):
    try:
        with connection.cursor() as cursor:
            # GET single row from schedH5 table
            _sql = """SELECT json_agg(t) FROM ( SELECT
            cmte_id,
            report_id,
            transaction_type_identifier ,
            transaction_id,
            account_name,
            receipt_date,
            total_amount_transferred,
            voter_registration_amount,
            voter_id_amount,
            gotv_amount,
            generic_campaign_amount,
            memo_code,
            memo_text,
            line_number,
            transaction_type,
            create_date,
            last_update_date,
            coalesce(
                voter_registration_amount,
                voter_id_amount,
                gotv_amount,
                generic_campaign_amount) as transfer_amount,
            (
                CASE 
                WHEN  voter_registration_amount > 0  
                THEN 'Voter Registration'
                WHEN  voter_id_amount > 0 
                THEN 'Voter ID'
                WHEN  gotv_amount > 0
                THEN 'GOTV'
                ELSE 'Generic Campaign'
                END
            ) AS transfer_type
            FROM public.sched_h5
            WHERE report_id = %s AND cmte_id = %s
            AND delete_ind is distinct from 'Y') t
            """
            cursor.execute(_sql, (report_id, cmte_id))
            return cursor.fetchone()[0]
        #     if schedH5_list is None:
        #         raise NoOPError('No sched_H5 transaction found for report_id {} and cmte_id: {}'.format(
        #             report_id, cmte_id))
        #     merged_list = []
        #     for dictH5 in schedH5_list:
        #         merged_list.append(dictH5)
        # return merged_list
    except Exception:
        raise


def get_list_schedH5(report_id, cmte_id, transaction_id):
    try:
        with connection.cursor() as cursor:
            # GET single row from schedH5 table
            _sql = """SELECT json_agg(t) FROM ( SELECT
            cmte_id,
            report_id,
            transaction_type_identifier ,
            transaction_id,
            account_name,
            receipt_date,
            total_amount_transferred,
            voter_registration_amount,
            voter_id_amount,
            gotv_amount,
            generic_campaign_amount,
            memo_code,
            memo_text,
            line_number,
            transaction_type,
            back_ref_transaction_id,
            create_date,
            last_update_date,
            coalesce(
                voter_registration_amount,
                voter_id_amount,
                gotv_amount,
                generic_campaign_amount) as transfer_amount,
            (
                CASE 
                WHEN  voter_registration_amount > 0  
                THEN 'Voter Registration'
                WHEN  voter_id_amount > 0 
                THEN 'Voter ID'
                WHEN  gotv_amount > 0
                THEN 'GOTV'
                ELSE 'Generic Campaign'
                END
            ) AS transfer_type
            FROM public.sched_h5
            WHERE report_id = %s AND cmte_id = %s AND transaction_id = %s
            AND delete_ind is distinct from 'Y') t
            """
            cursor.execute(_sql, (report_id, cmte_id, transaction_id))
            return cursor.fetchone()[0]
    except Exception:
        raise


def delete_sql_schedH5(cmte_id, report_id, transaction_id):
    """
    do delete sql transaction
    """
    _sql = """UPDATE public.sched_h5
            SET delete_ind = 'Y' 
            WHERE transaction_id = %s AND report_id = %s AND cmte_id = %s
        """
    _v = (transaction_id, report_id, cmte_id)
    do_transaction(_sql, _v)


def delete_schedH5(data):
    """
    function for handling delete request for sh5
    """
    try:

        delete_sql_schedH5(
            data.get("cmte_id"), data.get("report_id"), data.get("transaction_id")
        )
    except Exception as e:
        raise


@api_view(["GET"])
def get_h5_summary(request):
    """
    get h5 summary for enabling summary page
    1. load only child items
    3. report_id based.

    # TODO: what is gonna happen when people click edit button? 
    """
    try:
    #: Get the request parameters and set for Pagination
        query_params = request.query_params
        page_num = get_int_value(query_params.get("page"))

        descending = query_params.get("descending")
        if not (
            "sortColumnName" in query_params
            and check_null_value(query_params.get("sortColumnName"))
        ):
            sortcolumn = "name"
        elif query_params.get("sortColumnName") == "default":
            sortcolumn = "name"
        else:
            sortcolumn = query_params.get("sortColumnName")
        itemsperpage =  get_int_value(query_params.get("itemsPerPage"))
        search_string = query_params.get("search")
        params = query_params.get("filters", {})
        keywords = params.get("keywords")
        if str(descending).lower() == "true":
            descending = "DESC"
        else:
            descending = "ASC"
        trans_query_string_count = ""
                
        #: Hardcode cmte value for now and remove after dev complete
        #cmte_id = "C00000935"
        cmte_id = get_comittee_id(request.user.username)
        report_id = request.query_params.get("report_id")
        # aggregate_dic = load_h3_aggregate_amount(cmte_id, report_id)

        with connection.cursor() as cursor:
            # GET single row from schedA table
            _sql = """SELECT json_agg(t) FROM ( SELECT
            transaction_id,
            back_ref_transaction_id,
            account_name,
            receipt_date,
            total_amount_transferred,
            memo_text,
            coalesce(
                voter_registration_amount,
                voter_id_amount,
                gotv_amount,
                generic_campaign_amount) as transfer_amount,
            (
                CASE 
                WHEN  voter_registration_amount > 0  
                THEN 'Voter Registration'
                WHEN  voter_id_amount > 0 
                THEN 'Voter ID'
                WHEN  gotv_amount > 0
                THEN 'GOTV'
                ELSE 'Generic Campaign'
                END
            ) AS transfer_type
            FROM public.sched_h5
            WHERE report_id = %s AND cmte_id = %s
            --AND back_ref_transaction_id is not null
            AND delete_ind is distinct from 'Y') t
            """
            cursor.execute(_sql, (report_id, cmte_id))
            # print(_sql)
            # cursor.execute(_sql)
            _sum = cursor.fetchone()[0]
            # for _rec in _sum:
            #     if _rec['activity_event_name']:
            #         _rec['aggregate_amount'] = aggregate_dic.get(_rec['activity_event_name'])
            #     elif _rec['activity_event_type']:
            #         _rec['aggregate_amount'] = aggregate_dic.get(_rec['activity_event_type'])
            #     else:
            #         pass
            
            #: update for pagination
            json_result = get_pagination_dataset(_sum, itemsperpage, page_num)
            return Response(json_result, status=status.HTTP_200_OK)
    except:
        raise


@api_view(["GET"])
def get_sched_h5_breakdown(request):
    """
    api to get h5 sum values group by activity categories
    request parameters: cmte_id, report_id
    retrun:

    """
    _sql = """
    SELECT json_agg(t) FROM(
        select
        sum(voter_id_amount) as voter_id,
        sum(voter_registration_amount) as voter_registration,
        sum(gotv_amount) as gotv,
        sum(generic_campaign_amount) as generic_campaign
        from public.sched_h5
        where report_id = %s
        and cmte_id = %s
        and delete_ind is distinct from 'Y'
    ) t
    """
    try:
        cmte_id = get_comittee_id(request.user.username)
        if not ("report_id" in request.query_params):
            raise Exception("Missing Input: Report_id is mandatory")
        # handling null,none value of report_id
        if not (check_null_value(request.query_params.get("report_id"))):
            report_id = "0"
        else:
            report_id = check_report_id(request.query_params.get("report_id"))
        with connection.cursor() as cursor:
            cursor.execute(_sql, [report_id, cmte_id])
            result = cursor.fetchone()[0]
            # print(result)
            # if none returned, set it to 0
            # TODO: make this code a little more elegent by re-define handshaking with frontend
            _t = {k: 0 for k, v in result[0].items() if not v}
            result[0].update(_t)
            result[0]["total"] = (
                    float(result[0].get("voter_id", 0))
                    + float(result[0].get("voter_registration", 0))
                    + float(result[0].get("gotv", 0))
                    + float(result[0].get("generic_campaign", 0))
            )
        return Response(result, status=status.HTTP_200_OK)
    except Exception as e:
        raise Exception("Error on fetching h5 break down")


@api_view(["POST", "GET", "DELETE", "PUT"])
def schedH5(request):
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
                datum = schedH5_sql_dict(request.data)
                datum["report_id"] = report_id
                datum["cmte_id"] = cmte_id
                if "transaction_id" in request.data and check_null_value(
                        request.data.get("transaction_id")
                ):
                    datum["transaction_id"] = check_transaction_id(
                        request.data.get("transaction_id")
                    )
                    data = put_schedH5(datum)
                    if "child" in request.data:
                        for _c in request.data["child"]:
                            child_data = data
                            child_data.update(_c)
                            child_data["back_ref_transaction_id"] = data["transaction_id"]
                            child_data = schedH5_sql_dict(child_data)
                            child_data["cmte_id"] = cmte_id
                            child_data["report_id"] = report_id
                            logger.debug(
                                "saving child transaction with data {}".format(child_data)
                            )
                            post_schedH5(child_data)
                else:
                    # print('---')
                    # print(datum)
                    data = post_schedH5(datum)
                    logger.debug("parent data saved:{}".format(data))
                    if "child" in request.data:
                        for _c in request.data["child"]:
                            child_data = data.copy()
                            child_data.update(_c)
                            child_data["back_ref_transaction_id"] = data["transaction_id"]
                            child_data = schedH5_sql_dict(child_data)
                            child_data["cmte_id"] = cmte_id
                            child_data["report_id"] = report_id
                            logger.debug(
                                "saving child transaction with data {}".format(child_data)
                            )
                            post_schedH5(child_data)
                # Associating child transactions to parent and storing them to DB

                output = get_schedH5(data)
                return JsonResponse(output[0], status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response(
                    "The schedH5 API - POST is throwing an exception: " + str(e),
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
                datum = get_schedH5(data)
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
                    "The schedH5 API - GET is throwing an error: " + str(e),
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
                delete_schedH5(data)
                return Response(
                    "The Transaction ID: {} has been successfully deleted".format(
                        data.get("transaction_id")
                    ),
                    status=status.HTTP_201_CREATED,
                )
            except Exception as e:
                return Response(
                    "The schedH5 API - DELETE is throwing an error: " + str(e),
                    status=status.HTTP_400_BAD_REQUEST,
                )

        elif request.method == "PUT":
            try:
                datum = schedH5_sql_dict(request.data)
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

                # if 'entity_id' in request.data and check_null_value(request.data.get('entity_id')):
                #     datum['entity_id'] = request.data.get('entity_id')
                # if request.data.get('transaction_type') in CHILD_SCHED_B_TYPES:
                #     data = put_schedB(datum)
                #     output = get_schedB(data)
                # else:
                data = put_schedH5(datum)
                # output = get_schedH5(data)
                return JsonResponse(data, status=status.HTTP_201_CREATED, safe=False)
            except Exception as e:
                logger.debug(e)
                return Response(
                    "The schedH5 API - PUT is throwing an error: " + str(e),
                    status=status.HTTP_400_BAD_REQUEST,
                )

    except Exception as e:
        json_result = {'message': str(e)}
        return JsonResponse(json_result, status=status.HTTP_403_FORBIDDEN, safe=False)


"""


**********************************************************CRUD API FOR SCHEDULE_H6*********************************************************************************
"""


def check_mandatory_fields_SH6(data):
    """
    validate mandatory fields for sched_H6 item
    """
    try:
        errors = []
        for field in MANDATORY_FIELDS_SCHED_H6:
            if not (field in data and check_null_value(data.get(field))):
                errors.append(field)
        if errors:
            raise Exception(
                "The following mandatory fields are required in order to save data to schedH6 table: {}".format(
                    ",".join(errors)
                )
            )
    except:
        raise


def schedH6_sql_dict(data):
    """
    filter out valid fileds for sched_H6

    """
    valid_fields = [
        "line_number",
        "transaction_type_identifier",
        "transaction_type",
        "back_ref_transaction_id",
        "back_ref_sched_name",
        "entity_id",
        "account_event_identifier",
        "expenditure_date",
        "total_fed_levin_amount",
        "federal_share",
        "levin_share",
        "activity_event_total_ytd",
        "expenditure_purpose",
        "category_code",
        "activity_event_type",
        "memo_code",
        "memo_text",
        "aggregation_ind",
        # 'create_date',
        # 'last_update_date',
        # entity_data
        "entity_id",
        "entity_type",
        "entity_name",
        "first_name",
        "last_name",
        "middle_name",
        "preffix",
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
        line_num, tran_tp = get_line_number_trans_type(
            data["transaction_type_identifier"]
        )
        valid_data["line_number"] = line_num
        valid_data["transaction_type"] = tran_tp

        # TODO; tmp chagne, need to remove those code when db schema corrected
        if "total_amount" in data:
            valid_data["total_fed_levin_amount"] = data.get("total_amount")
        if "fed_share_amount" in data:
            valid_data["federal_share"] = data.get("fed_share_amount")
        if "non_fed_share_amount" in data:
            valid_data["levin_share"] = data.get("non_fed_share_amount")
        if "activity_event_amount_ytd" in data:
            valid_data["activity_event_total_ytd"] = data.get(
                "activity_event_amount_ytd"
            )

        return valid_data
    except:
        raise Exception("invalid request data.")


def get_existing_h6_total(cmte_id, transaction_id):
    """
    fetch existing close balance in the db for current transaction
    """
    _sql = """
    select total_fed_levin_amount
    from public.sched_h6
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
def put_schedH6(data):
    """
    update sched_H6 item
    """
    try:
        check_mandatory_fields_SH6(data)
        if "entity_id" in data:
            get_data = {
                "cmte_id": data.get("cmte_id"),
                "entity_id": data.get("entity_id"),
            }

            # need this update for FEC entity
            if get_data["entity_id"].startswith("FEC"):
                get_data["cmte_id"] = "C00000000"

            prev_entity_list = get_entities(get_data)
            entity_data = put_entities(data)
            roll_back = True
        else:
            entity_data = post_entities(data)
            roll_back = False
        # check_transaction_id(data.get('transaction_id'))
        existing_total = get_existing_h6_total(
            data.get("cmte_id"), data.get("transaction_id")
        )
        try:
            put_sql_schedH6(data)
            # update ytd aggregation if not memo transaction
            if not data.get("transaction_type_identifier").endswith("_MEMO"):
                update_activity_event_amount_ytd_h6(data)
            update_activity_event_amount_ytd_h6(data)

            # if debt payment, update parent sched_d
            if data.get("transaction_type_identifier") == "ALLOC_FEA_DISB_DEBT":
                if float(existing_total) != float(data.get("total_fed_levin_amount")):
                    update_sched_d_parent(
                        data.get("cmte_id"),
                        data.get("back_ref_transaction_id"),
                        data.get("total_fed_levin_amount"),
                        existing_total,
                    )

        except Exception as e:
            if roll_back:
                entity_data = put_entities(prev_entity_list[0])
            else:
                get_data = {"cmte_id": data.get("cmte_id"), "entity_id": entity_id}
                remove_entities(get_data)
            raise Exception(
                "The put_sql_schedH6 function is throwing an error: " + str(e)
            )
        return data
    except:
        raise


def put_sql_schedH6(data):
    """
    update a schedule_H6 item                    
            
    """
    _sql = """UPDATE public.sched_h6
              SET line_number = %s,
                  transaction_type_identifier= %s,
                  transaction_type = %s,
                  back_ref_transaction_id = %s,
                  back_ref_sched_name = %s,
                  entity_id = %s,
                  account_event_identifier = %s,
                  expenditure_date = %s,
                  total_fed_levin_amount = %s,
                  federal_share  = %s,
                  levin_share  = %s,
                  activity_event_total_ytd = %s,
                  expenditure_purpose = %s,
                  category_code = %s,
                  activity_event_type = %s,
                  memo_code = %s,
                  memo_text = %s,
                  aggregation_ind = %s,
                  last_update_date= %s
              WHERE transaction_id = %s AND report_id = %s AND cmte_id = %s 
              AND delete_ind is distinct from 'Y';
        """
    _v = (
        data.get("line_number"),
        data.get("transaction_type_identifier"),
        data.get("transaction_type"),
        data.get("back_ref_transaction_id"),
        data.get("back_ref_sched_name"),
        data.get("entity_id"),
        data.get("account_event_identifier"),
        data.get("expenditure_date"),
        data.get("total_fed_levin_amount"),
        data.get("federal_share"),
        data.get("levin_share"),
        data.get("activity_event_total_ytd"),
        data.get("expenditure_purpose"),
        data.get("category_code"),
        data.get("activity_event_type"),
        data.get("memo_code"),
        data.get("memo_text"),
        data.get("aggregation_ind"),
        datetime.datetime.now(),
        data.get("transaction_id"),
        data.get("report_id"),
        data.get("cmte_id"),
    )
    do_transaction(_sql, _v)


def validate_sh6_data(data):
    """
    validate sH6 json data
    """
    check_mandatory_fields_SH6(data)
    for _rec in ["levin_share", "federal_share", "total_fed_levin_amount"]:
        if "," in str(data.get(_rec, "")):
            # logger.debug(data.get(_rec))
            data[_rec] = data[_rec].replace(",", "")


def post_sql_schedH6(data):
    try:
        _sql = """
        INSERT INTO public.sched_h6 ( 
            cmte_id,
            report_id,
            line_number,
            transaction_type_identifier,
            transaction_type,
            transaction_id,
            back_ref_transaction_id,
            back_ref_sched_name,
            entity_id,
            account_event_identifier,
            expenditure_date,
            total_fed_levin_amount,
            federal_share,
            levin_share,
            activity_event_total_ytd,
            expenditure_purpose,
            category_code,
            activity_event_type,
            memo_code,
            memo_text,
            aggregation_ind,
            create_date
         )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s); 
        """
        _v = (
            data.get("cmte_id"),
            data.get("report_id"),
            data.get("line_number"),
            data.get("transaction_type_identifier"),
            data.get("transaction_type"),
            data.get("transaction_id"),
            data.get("back_ref_transaction_id"),
            data.get("back_ref_sched_name"),
            data.get("entity_id"),
            data.get("account_event_identifier"),
            data.get("expenditure_date"),
            data.get("total_fed_levin_amount"),
            data.get("federal_share"),
            data.get("levin_share"),
            data.get("activity_event_total_ytd"),
            data.get("expenditure_purpose"),
            data.get("category_code"),
            data.get("activity_event_type"),
            data.get("memo_code"),
            data.get("memo_text"),
            data.get("aggregation_ind"),
            datetime.datetime.now(),
        )
        with connection.cursor() as cursor:
            # Insert data into schedH6 table
            cursor.execute(_sql, _v)
    except Exception:
        raise


def list_all_transactions_event_type_h6(start_dt, end_dt, activity_event_type, cmte_id):
    """
    load all transactions with the specified activity event type
    need to check
    """
    logger.debug(
        "load transactions with activity_event_type:{}".format(activity_event_type)
    )
    # logger.debug('load ttransactionsransactions with start:{}, end {}'.format(start_dt, end_dt))
    # logger.debug('load ttransactionsransactions with cmte-id:{}'.format(cmte_id))
    _sql = """
            SELECT t1.total_fed_levin_amount, 
                t1.transaction_id,
                t1.aggregation_ind
            FROM public.sched_h6 t1 
            WHERE activity_event_type = %s 
            AND cmte_id = %s
            AND expenditure_date >= %s
            AND expenditure_date <= %s 
            AND back_ref_transaction_id is null
            AND delete_ind is distinct FROM 'Y' 
            ORDER BY expenditure_date ASC, create_date ASC
    """
    # .format(activity_event_type, cmte_id, start_dt, end_dt)
    # logger.debug(_sql)
    try:
        with connection.cursor() as cursor:
            cursor.execute(_sql, (activity_event_type, cmte_id, start_dt, end_dt))
            # , [
            #         activity_event_type,
            #         cmte_id,
            #         start_dt,
            #         end_dt,
            #     ])
            transactions_list = cursor.fetchall()
            logger.debug("transaction fetched:{}".format(transactions_list))
        return transactions_list
    except Exception as e:
        raise Exception(
            "The list_all_transactions_event_type function is throwing an error: "
            + str(e)
        )


def update_transaction_ytd_amount_h6(cmte_id, transaction_id, aggregate_amount):
    """
    update h4 ytd amount
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """ UPDATE public.sched_h6
                    SET activity_event_total_ytd = %s 
                    WHERE transaction_id = %s AND cmte_id = %s AND delete_ind is distinct from 'Y'
                    """,
                [aggregate_amount, transaction_id, cmte_id],
            )
            if cursor.rowcount == 0:
                raise Exception(
                    "Error: The Transaction ID: {} does not exist in sched_h6 table".format(
                        transaction_id
                    )
                )
    except Exception:
        raise


def update_activity_event_amount_ytd_h6(data):
    """
    aggregate and update 'activity_event_amount_ytd' for all h6 transactions
    """
    try:

        logger.debug("updating ytd amount h6:")
        # make sure transaction list comes back sorted by contribution_date ASC
        expenditure_dt = date_format(data.get("expenditure_date"))
        aggregate_start_date = datetime.date(expenditure_dt.year, 1, 1)
        aggregate_end_date = datetime.date(expenditure_dt.year, 12, 31)
        transactions_list = list_all_transactions_event_type_h6(
            aggregate_start_date,
            aggregate_end_date,
            data.get("activity_event_type"),
            data.get("cmte_id"),
        )
        aggregate_amount = 0
        for transaction in transactions_list:
            if transaction[2] != "N":
                aggregate_amount += transaction[0]
            transaction_id = transaction[1]
            update_transaction_ytd_amount_h6(
                data.get("cmte_id"), transaction_id, aggregate_amount
            )
    except Exception as e:
        raise Exception(
            "The update_activity_event_amount_ytd function is throwing an error: "
            + str(e)
        )


@update_F3X
@new_report_date
def post_schedH6(data):
    """
    function for handling POST request for sH6, need to:
    1. generatye new transaction_id
    2. validate data
    3. save data to db
    """
    try:
        # check_mandatory_fields_SH6(datum, MANDATORY_FIELDS_SCHED_H6o)
        logger.debug("saving h6 with data:{}".format(data))
        if "entity_id" in data:
            get_data = {
                "cmte_id": data.get("cmte_id"),
                "entity_id": data.get("entity_id"),
            }

            # need this update for FEC entity
            if get_data["entity_id"].startswith("FEC"):
                get_data["cmte_id"] = "C00000000"

            prev_entity_list = get_entities(get_data)
            entity_data = put_entities(data)
            roll_back = True
        else:
            entity_data = post_entities(data)
            roll_back = False
        logger.debug("entity saved.")
        # continue to save transaction
        entity_id = entity_data.get("entity_id")
        data["entity_id"] = entity_id
        data["transaction_id"] = get_next_transaction_id("SH6")

        validate_sh6_data(data)
        try:
            post_sql_schedH6(data)
            # update ytd aggregation if not memo transaction
            # if not data.get("transaction_type_identifier").endswith("_MEMO"):
            update_activity_event_amount_ytd_h6(data)
            if data.get("transaction_type_identifier") == "ALLOC_FEA_DISB_DEBT":
                update_sched_d_parent(
                    data.get("cmte_id"),
                    data.get("back_ref_transaction_id"),
                    data.get("total_fed_levin_amount"),
                )
        except Exception as e:
            if roll_back:
                entity_data = put_entities(prev_entity_list[0])
            else:
                get_data = {"cmte_id": data.get("cmte_id"), "entity_id": entity_id}
                remove_entities(get_data)
            raise Exception(
                "The post_sql_schedH6 function is throwing an error: " + str(e)
            )
        return data
    except:
        raise


def get_schedH6(data):
    """
    load sched_H6 data based on cmte_id, report_id and transaction_id
    """
    try:
        cmte_id = data.get("cmte_id")
        report_id = data.get("report_id")

        if "transaction_id" in data:
            transaction_id = check_transaction_id(data.get("transaction_id"))
            # print('get_schedH6')
            forms_obj = get_list_schedH6(report_id, cmte_id, transaction_id)
        else:
            forms_obj = get_list_all_schedH6(report_id, cmte_id)

        # TODO: need to remove this when db correction done
        for obj in forms_obj:
            obj["api_call"] = "/sh6/schedH6"
            obj["fed_share_amount"] = obj.get("federal_share")
            obj["non_fed_share_amount"] = obj.get("levin_share")
            obj["total_amount"] = obj.get("total_fed_levin_amount")
            obj["activity_event_amount_ytd"] = obj.get("activity_event_total_ytd")
            child_data = get_sched_h6_child_transactions(
                obj.get("report_id"), obj.get("cmte_id"), obj.get("transaction_id")
            )
            if child_data:
                obj["child"] = child_data
        return forms_obj
    except:
        raise


def get_list_all_schedH6(report_id, cmte_id):
    try:
        with connection.cursor() as cursor:
            # GET single row from schedH6 table
            _sql = """SELECT json_agg(t) FROM ( SELECT
            cmte_id,
            report_id,
            line_number,
            transaction_type_identifier,
            transaction_type,
            transaction_id ,
            back_ref_transaction_id,
            back_ref_sched_name,
            entity_id,
            account_event_identifier,
            expenditure_date,
            total_fed_levin_amount,
            federal_share,
            levin_share,
            activity_event_total_ytd,
            expenditure_purpose,
            category_code,
            activity_event_type,
            memo_code,
            memo_text,
            aggregation_ind,
            create_date,
            last_update_date
            FROM public.sched_h6
            WHERE report_id = %s AND cmte_id = %s
            AND delete_ind is distinct from 'Y') t
            """
            cursor.execute(_sql, (report_id, cmte_id))
            schedH6_list = cursor.fetchone()[0]
            if schedH6_list is None:
                raise NoOPError(
                    "No sched_H6 transaction found for report_id {} and cmte_id: {}".format(
                        report_id, cmte_id
                    )
                )
            merged_list = []
            for tran in schedH6_list:
                entity_id = tran.get("entity_id")
                q_data = {"entity_id": entity_id, "cmte_id": cmte_id}
                dictEntity = get_entities(q_data)[0]
                merged_list.append({**tran, **dictEntity})
        return merged_list
    except Exception:
        raise


def get_list_schedH6(report_id, cmte_id, transaction_id):
    try:
        with connection.cursor() as cursor:
            # GET single row from schedH6 table
            _sql = """SELECT json_agg(t) FROM ( SELECT
            cmte_id,
            report_id,
            line_number,
            transaction_type_identifier,
            transaction_type,
            transaction_id ,
            back_ref_transaction_id,
            back_ref_sched_name,
            entity_id,
            account_event_identifier,
            expenditure_date,
            total_fed_levin_amount,
            federal_share,
            levin_share,
            activity_event_total_ytd,
            expenditure_purpose,
            category_code,
            activity_event_type,
            memo_code,
            memo_text,
            aggregation_ind,
            create_date,
            last_update_date
            FROM public.sched_h6
            WHERE report_id = %s AND cmte_id = %s AND transaction_id = %s
            AND delete_ind is distinct from 'Y') t
            """
            cursor.execute(_sql, (report_id, cmte_id, transaction_id))
            schedH6_list = cursor.fetchone()[0]
            if schedH6_list is None:
                raise NoOPError(
                    "No sched_H6 transaction found for transaction_id {}".format(
                        transaction_id
                    )
                )
            merged_list = []
            for tran in schedH6_list:
                entity_id = tran.get("entity_id")
                q_data = {"entity_id": entity_id, "cmte_id": cmte_id}
                dictEntity = get_entities(q_data)[0]
                merged_list.append({**tran, **dictEntity})
        return merged_list
    except Exception:
        raise


def delete_sql_schedH6(cmte_id, report_id, transaction_id):
    """
    do delete sql transaction
    """
    _sql = """UPDATE public.sched_h6
            SET delete_ind = 'Y' 
            WHERE transaction_id = %s AND report_id = %s AND cmte_id = %s
        """
    _v = (transaction_id, report_id, cmte_id)
    do_transaction(_sql, _v)


def delete_schedH6(data):
    """
    function for handling delete request for sh6
    """
    try:

        delete_sql_schedH6(
            data.get("cmte_id"), data.get("report_id"), data.get("transaction_id")
        )
    except Exception as e:
        raise


@api_view(["POST", "GET", "DELETE", "PUT"])
def schedH6(request):
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
                datum = schedH6_sql_dict(request.data)
                datum["report_id"] = report_id
                datum["cmte_id"] = cmte_id
                if "transaction_id" in request.data and check_null_value(
                        request.data.get("transaction_id")
                ):
                    datum["transaction_id"] = check_transaction_id(
                        request.data.get("transaction_id")
                    )
                    data = put_schedH6(datum)
                else:
                    # print(datum)
                    print("post new h6 with data:{}".format(datum))
                    data = post_schedH6(datum)
                # Associating child transactions to parent and storing them to DB
                output = get_schedH6(data)

                return JsonResponse(output[0], status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response(
                    "The schedH6 API - POST is throwing an exception: " + str(e),
                    status=status.HTTP_400_BAD_REQUEST,
                )

                return JsonResponse(output[0], status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response(
                    "The schedH6 API - POST is throwing an exception: " + str(e),
                    status=status.HTTP_400_BAD_REQUEST,
                )

        elif request.method == "GET":
            try:
                #: Get the request parameters and set for Pagination
                query_params = request.query_params
                page_num = get_int_value(query_params.get("page"))

                descending = query_params.get("descending")
                if not (
                    "sortColumnName" in query_params
                    and check_null_value(query_params.get("sortColumnName"))
                ):
                    sortcolumn = "name"
                elif query_params.get("sortColumnName") == "default":
                    sortcolumn = "name"
                else:
                    sortcolumn = query_params.get("sortColumnName")
                itemsperpage =  get_int_value(query_params.get("itemsPerPage"))
                search_string = query_params.get("search")
                params = query_params.get("filters", {})
                keywords = params.get("keywords")
                if str(descending).lower() == "true":
                    descending = "DESC"
                else:
                    descending = "ASC"
                trans_query_string_count = ""
                        
                #: Hardcode cmte value for now and remove after dev complete
                #data = {"cmte_id": "C00000935"}
                data = {"cmte_id": get_comittee_id(request.user.username)}
                # make sure we get query parameters from both
                # request.data.update(request.query_params)
                if "report_id" in request.query_params and check_null_value(
                    request.query_params.get("report_id")
                ):
                    data["report_id"] = check_report_id(
                        request.query_params.get("report_id")
                )

                datum = get_schedH6(data)

                #: update for pagination
                json_result = get_pagination_dataset(datum, itemsperpage, page_num)
                return Response(json_result, status=status.HTTP_200_OK)
            except NoOPError as e:
                logger.debug(e)
                #: tobe removed after development testing for 
                forms_obj =  {
                    "transactions": "",
                    "totaltransactionsCount": "",
                    "itemsPerPage": "",
                    "pageNumber": "",
                    "totalPages": "",
                }
                return JsonResponse(
                    forms_obj, status=status.HTTP_200_OK, safe=False
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
                delete_schedH6(data)
                return Response(
                    "The Transaction ID: {} has been successfully deleted".format(
                        data.get("transaction_id")
                    ),
                    status=status.HTTP_201_CREATED,
                )
            except Exception as e:
                return Response(
                    "The schedH6 API - DELETE is throwing an error: " + str(e),
                    status=status.HTTP_400_BAD_REQUEST,
                )

        elif request.method == "PUT":
            try:
                datum = schedH6_sql_dict(request.data)
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

                # if 'entity_id' in request.data and check_null_value(request.data.get('entity_id')):
                #     datum['entity_id'] = request.data.get('entity_id')
                # if request.data.get('transaction_type') in CHILD_SCHED_B_TYPES:
                #     data = put_schedB(datum)
                #     output = get_schedB(data)
                # else:
                data = put_schedH6(datum)
                output = get_schedH6(data)
                return JsonResponse(output[0], status=status.HTTP_201_CREATED)
            except Exception as e:
                logger.debug(e)
                return Response(
                    "The schedH6 API - PUT is throwing an error: " + str(e),
                    status=status.HTTP_400_BAD_REQUEST,
                )

    except Exception as e:
        json_result = {'message': str(e)}
        return JsonResponse(json_result, status=status.HTTP_403_FORBIDDEN, safe=False)
