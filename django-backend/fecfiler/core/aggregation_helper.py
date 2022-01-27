import logging
import datetime
import requests

# from functools import lru_cache
from django.db import connection
from fecfiler.core.transaction_util import do_transaction
from fecfiler.core.views import cmte_type, update_F3X, find_form_type


# from fecfiler.core.views import get_entities, NoOPError, superceded_report_id_list
# import datetime

logger = logging.getLogger(__name__)

PTY_AGGREGATE_TYPES_HQ = [
    "IND_NP_HQ_ACC",
    "PARTY_NP_HQ_ACC",
    "PAC_NP_HQ_ACC",
    "TRIB_NP_HQ_ACC",
    "EAR_REC_HQ_ACC",
    "JF_TRAN_NP_HQ_IND_MEMO",
    "JF_TRAN_NP_HQ_PAC_MEMO",
    "JF_TRAN_NP_HQ_TRIB_MEMO",
    "OPEXP_HQ_ACC_REG_REF",
    "OPEXP_HQ_ACC_IND_REF",
    "OPEXP_HQ_ACC_TRIB_REF",
]

PTY_AGGREGATE_TYPES_CO = [
    "IND_NP_CONVEN_ACC",
    "PARTY_NP_CONVEN_ACC",
    "PAC_NP_CONVEN_ACC",
    "TRIB_NP_CONVEN_ACC",
    "EAR_REC_CONVEN_ACC",
    "JF_TRAN_NP_CONVEN_IND_MEMO",
    "JF_TRAN_NP_CONVEN_PAC_MEMO",
    "JF_TRAN_NP_CONVEN_TRIB_MEMO",
    "OPEXP_CONV_ACC_REG_REF",
    "OPEXP_CONV_ACC_TRIB_REF",
    "OPEXP_CONV_ACC_IND_REF",
]

PTY_AGGREGATE_TYPES_NPRE = [
    "IND_NP_RECNT_ACC",
    "TRIB_NP_RECNT_ACC",
    "PARTY_NP_RECNT_ACC",
    "PAC_NP_RECNT_ACC",
    "EAR_REC_RECNT_ACC",
    "JF_TRAN_NP_RECNT_IND_MEMO",
    "JF_TRAN_NP_RECNT_PAC_MEMO",
    "JF_TRAN_NP_RECNT_TRIB_MEMO",
    "OTH_DISB_NP_RECNT_REG_REF",
    "OTH_DISB_NP_RECNT_TRIB_REF",
    "OTH_DISB_NP_RECNT_IND_REF",
]

PTY_AGGREGATE_TYPES_RE = [
    "IND_RECNT_REC",
    "PARTY_RECNT_REC",
    "PAC_RECNT_REC",
    "TRIB_RECNT_REC",
]

PAC_AGGREGATE_TYPES_1 = [
    "IND_REC_NON_CONT_ACC",
    "OTH_CMTE_NON_CONT_ACC",
    "BUS_LAB_NON_CONT_ACC",
]

# list of all transaction type identifiers that should auto generate sched_b item in DB
AUTO_GENERATE_SCHEDB_PARENT_CHILD_TRANSTYPE_DICT = {
    "IK_REC": "IK_OUT",
    "IK_BC_REC": "IK_BC_OUT",
    # "CON_EAR_DEP" : "CON_EAR_DEP_MEMO",
    # "CON_EAR_UNDEP" : "CON_EAR_UNDEP_MEMO",
    "PARTY_IK_REC": "PARTY_IK_OUT",
    "PARTY_IK_BC_REC": "PARTY_IK_BC_OUT",
    "PAC_IK_REC": "PAC_IK_OUT",
    "PAC_IK_BC_REC": "PAC_IK_BC_OUT",
    # "PAC_CON_EAR_DEP" : "PAC_CON_EAR_DEP_OUT",
    # "PAC_CON_EAR_UNDEP" : "PAC_CON_EAR_UNDEP_MEMO",
    "IK_TRAN": "IK_TRAN_OUT",
    "IK_TRAN_FEA": "IK_TRAN_FEA_OUT",
}

# list of all transaction type identifiers that have itemization rule applied to it
# TODO: need to update this list: PAR_CON?, PAR_MEMO?, REATT_TO?
# ITEMIZATION_TRANSACTION_TYPE_IDENTIFIER_LIST = [
#     "INDV_REC",
#     "PAR_CON",
#     "PAR_MEMO",
#     "IK_REC",
#     "REATT_FROM",
#     "REATT_TO",
# ]
# itemization rules updated against the newest version of spreadsheet
ITEMIZATION_TRANSACTION_TYPE_IDENTIFIER_LIST = [
    "TRIB_REC",
    "IK_REC",
    "IK_BC_REC",
    "PARTN_MEMO",
    "BC_TO_IND_MEMO",
    "BC_TO_UNKN_MEMO",
    "INDV_REC",
    "PARTN_REC",
    "REATT_FROM",
    "REATT_TO",
    "RET_REC",
    "BC_TO_IND",
    "BC_TO_UNKN",
    "PAC_NON_FED_RET",
    "PAC_NON_FED_REC",
]

# Updating itemized_ind for the below list
ITEMIZED_IND_UPDATE_TRANSACTION_TYPE_IDENTIFIER = [
    "TRIB_REC",
    "IK_REC",
    "IK_BC_REC",
    "PARTN_MEMO",
    "BC_TO_IND_MEMO",
    "BC_TO_UNKN_MEMO",
    "INDV_REC",
    "PARTN_REC",
    "REATT_FROM",
    "REATT_TO",
    "RET_REC",
    "BC_TO_IND",
    "BC_TO_UNKN",
    "IND_NP_HQ_ACC",
    "TRIB_NP_HQ_ACC",
    "IND_NP_CONVEN_ACC",
    "TRIB_NP_CONVEN_ACC",
    "EAR_REC_RECNT_ACC",
    "EAR_REC_CONVEN_ACC",
    "EAR_REC_HQ_ACC",
    "IND_REC_NON_CONT_ACC",
    "BUS_LAB_NON_CONT_ACC",
    "OFFSET_TO_OPEX",
    "TRIB_NP_RECNT_ACC",
    "IND_NP_RECNT_ACC",
    "IND_RECNT_REC",
    "OTH_REC",
    "OTH_REC_DEBT",
    "PAC_NON_FED_RET",
    "PAC_NON_FED_REC",
]

AUTO_GENERATE_SCHEDA_PARENT_CHILD_TRANSTYPE_DICT = {}


def date_agg_format(cvg_date):
    try:
        if cvg_date == None or cvg_date in ["none", "null", " ", ""]:
            return None
        cvg_dt = datetime.datetime.strptime(cvg_date, "%Y-%m-%d").date()
        return cvg_dt
    except:
        raise


def list_all_transactions_entity_lb(
    aggregate_start_date, aggregate_end_date, entity_id, cmte_id, levin_account_id
):
    """
    load all transactions for an entity within a time window
    return value: a list of transction_records [
       (contribution_amount, transaction_id, report_id, line_number, contribution_date),
       ....
    ]
    return items are sorted by contribution_date in ASC order
    """
    logger.debug(
        "fetching transactions for entity {} and levin acct {}".format(
            entity_id, levin_account_id
        )
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
            SELECT t1.expenditure_amount, 
                t1.transaction_id, 
                t1.report_id, 
                t1.line_number, 
                t1.expenditure_date, 
                (SELECT t2.delete_ind FROM public.reports t2 WHERE t2.report_id = t1.report_id), 
                t1.memo_code, 
                t1.back_ref_transaction_id,
                t1.transaction_type_identifier,
                t1.aggregation_ind
            FROM public.sched_b t1 
            WHERE entity_id = %s 
            AND cmte_id = %s 
            AND expenditure_date >= %s 
            AND expenditure_date <= %s
            AND levin_account_id = %s 
            AND delete_ind is distinct FROM 'Y' 
            ORDER BY expenditure_date ASC, create_date ASC
            """,
                [
                    entity_id,
                    cmte_id,
                    aggregate_start_date,
                    aggregate_end_date,
                    levin_account_id,
                ],
            )
            transactions_list = cursor.fetchall()
        logger.debug("transaction list loaded.")
        return transactions_list
    except Exception as e:
        raise Exception(
            "The list_all_transactions_entity function is throwing an error: " + str(e)
        )


def list_all_transactions_entity_la(
    aggregate_start_date, aggregate_end_date, entity_id, cmte_id, levin_account_id
):
    """
    load all transactions for an entity within a time window
    return value: a list of transction_records [
       (contribution_amount, transaction_id, report_id, line_number, contribution_date),
       ....
    ]
    return items are sorted by contribution_date in ASC order
    """
    logger.debug(
        "fetching transactions for entity {} and levin acct {}".format(
            entity_id, levin_account_id
        )
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
            SELECT t1.contribution_amount, 
                t1.transaction_id, 
                t1.report_id, 
                t1.line_number, 
                t1.contribution_date, 
                (SELECT t2.delete_ind FROM public.reports t2 WHERE t2.report_id = t1.report_id), 
                t1.memo_code, 
                t1.back_ref_transaction_id,
                t1.transaction_type_identifier,
                t1.aggregation_ind
            FROM public.sched_a t1 
            WHERE entity_id = %s 
            AND cmte_id = %s 
            AND contribution_date >= %s 
            AND contribution_date <= %s
            AND levin_account_id = %s 
            AND delete_ind is distinct FROM 'Y' 
            ORDER BY contribution_date ASC, create_date ASC
            """,
                [
                    entity_id,
                    cmte_id,
                    aggregate_start_date,
                    aggregate_end_date,
                    levin_account_id,
                ],
            )
            transactions_list = cursor.fetchall()
        logger.debug("transaction list loaded.")
        return transactions_list
    except Exception as e:
        raise Exception(
            "The list_all_transactions_entity function is throwing an error: " + str(e)
        )


def put_sql_agg_amount_schedA(
    cmte_id, transaction_id, aggregate_amount, itemized_ind
):
    """
    update aggregate amount
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE public.sched_a 
                SET aggregate_amt = %s,
                    itemized_ind = %s
                WHERE transaction_id = %s 
                AND cmte_id = %s 
                AND delete_ind is distinct from 'Y'
                """,
                [aggregate_amount, itemized_ind, transaction_id, cmte_id],
            )
            if cursor.rowcount == 0:
                raise Exception(
                    "put_sql_agg_amount_schedA function: The Transaction ID: {} does not exist in schedA table".format(
                        transaction_id
                    )
                )
        logger.debug(
            "***put_sql_agg_amount_schedA done with:{}".format(aggregate_amount)
        )
    except Exception:
        raise


def update_aggregate_la(datum):
    """
    helper function for updating private contribution line number based on aggrgate amount
    the aggregate amount is a contribution_date-based incremental update, the line number
    is updated accordingly:
    edit 1: check if the report corresponding to the transaction is deleted or not (delete_ind flag in reports table) 
            and only when it is NOT add contribution_amount to aggregate amount
    edit 2: updation of aggregate amount will roll to all transacctions irrespective of report id and report being filed
    edit 3: if back_ref_transaction_id is none, then check if memo_code is NOT 'X' and if it is not, add contribution_amount to aggregate amount; 
            if back_ref_transaction_id is NOT none, then add irrespective of memo_code, add contribution_amount to aggregate amount
    e.g.
    date, contribution_amount, aggregate_amount, line_number
    1/1/2018, 50, 50
    2/1/2018, 60, 110
    3/1/2018, 100, 210 (aggregate_amount > 200, transaction becomes itemized)
    """
    logger.debug("update sla aggregate with data {}".format(datum))
    # TODO need to set memo transaction aggregate to parent one
    if datum.get("transaction_id").endswith("_MEMO"):
        return

    # TODO need to set the aggregate to most recent transaction??? need confirmation on this
    if datum.get("memo_code") == "X":
        return
    try:
        # logger("update sla aggregate with data {}".format(datum))
        cmte_id = datum.get("cmte_id")
        report_id = datum.get("report_id")
        entity_id = datum.get("entity_id")
        levin_account_id = datum.get("levin_account_id")
        contribution_date = datum.get("contribution_date")
        child_flag_SB = False
        child_flag_SA = False
        itemization_value = 200
        form_type = find_form_type(report_id, cmte_id)
        if isinstance(contribution_date, str):
            contribution_date = date_agg_format(contribution_date)
        aggregate_start_date, aggregate_end_date = find_aggregate_date(
            form_type, contribution_date
        )
        transactions_list = list_all_transactions_entity_la(
            aggregate_start_date,
            aggregate_end_date,
            entity_id,
            cmte_id,
            levin_account_id,
        )
        if not transactions_list:
            return
        aggregate_amount = 0
        itemized_ind = ""
        output_line_number = ""
        for transaction in transactions_list:
            if transaction[5] != "Y":
                if not transaction[9] == "N":
                    aggregate_amount += transaction[0]
                    if aggregate_amount <= itemization_value:
                        itemized_ind = "U"
                    else:
                        itemized_ind = "I"

                # if transaction[7] != None or (
                #     transaction[7] == None and transaction[6] != "X"
                # ):
                # aggregate_amount += transaction[0]

                if contribution_date <= transaction[4]:
                    transaction_id = transaction[1]
                    put_sql_agg_amount_schedA(
                        cmte_id,
                        transaction_id,
                        aggregate_amount,
                        itemized_ind,
                    )

                    # child_SA_transaction_list = get_list_agg_child_schedA(report_id, cmte_id, transaction[1])
                    # for child_SA_transaction in child_SA_transaction_list:
                    #     put_sql_agg_amount_schedA(cmte_id, child_SA_transaction.get('transaction_id'), aggregate_amount)
                # #Updating aggregate amount to child auto generate sched B transactions
                # if child_flag_SB:
                #     child_SB_transaction_list = get_list_child_transactionId_schedB(cmte_id, transaction[1])
                #     for child_SB_transaction in child_SB_transaction_list:
                #         put_sql_agg_amount_schedB(cmte_id, child_SB_transaction[0], aggregate_amount)

    except Exception as e:
        raise Exception(
            "The update_aggregate_la function is throwing an error: " + str(e)
        )


# def list_all_transactions_entity_lb(
#     aggregate_start_date, aggregate_end_date, entity_id, cmte_id, levin_account_id
# ):
#     """
#     load all transactions for an entity within a time window
#     return value: a list of transction_records [
#        (contribution_amount, transaction_id, report_id, line_number, contribution_date),
#        ....
#     ]
#     return items are sorted by contribution_date in ASC order
#     """
#     logger.debug(
#         "fetching transactions for entity {} and levin acct {}".format(
#             entity_id, levin_account_id
#         )
#     )
#     try:
#         with connection.cursor() as cursor:
#             cursor.execute(
#                 """
#             SELECT t1.expenditure_amount,
#                 t1.transaction_id,
#                 t1.report_id,
#                 t1.line_number,
#                 t1.expenditure_date,
#                 (SELECT t2.delete_ind FROM public.reports t2 WHERE t2.report_id = t1.report_id),
#                 t1.memo_code,
#                 t1.back_ref_transaction_id,
#                 t1.transaction_type_identifier,
#                 t1.aggregation_ind
#             FROM public.sched_a t1
#             WHERE entity_id = %s
#             AND cmte_id = %s
#             AND expenditure_date >= %s
#             AND expenditure_date <= %s
#             AND levin_account_id = %s
#             AND delete_ind is distinct FROM 'Y'
#             ORDER BY expenditure_date ASC, create_date ASC
#             """,
#                 [
#                     entity_id,
#                     cmte_id,
#                     aggregate_start_date,
#                     aggregate_end_date,
#                     levin_account_id,
#                 ],
#             )
#             transactions_list = cursor.fetchall()
#         logger.debug("transaction list loaded.")
#         return transactions_list
#     except Exception as e:
#         raise Exception(
#             "The list_all_transactions_entity function is throwing an error: " + str(e)
#         )


def update_aggregate_lb(datum):
    """
    helper function for LB aggregation (aggregate_amount > 200, transaction becomes itemized)
    """
    logger.debug("update slb aggregate with data {}".format(datum))
    # TODO need to set memo transaction aggregate to parent one
    if datum.get("transaction_id").endswith("_MEMO"):
        return

    # TODO need to set the aggregate to most recent transaction??? need confirmation on this
    if datum.get("memo_code") == "X":
        return
    try:
        # logger("update sla aggregate with data {}".format(datum))
        cmte_id = datum.get("cmte_id")
        report_id = datum.get("report_id")
        entity_id = datum.get("entity_id")
        levin_account_id = datum.get("levin_account_id")
        expenditure_date = datum.get("expenditure_date")
        # child_flag_SB = False
        # child_flag_SA = False
        itemization_value = 200
        form_type = find_form_type(report_id, cmte_id)
        if isinstance(expenditure_date, str):
            expenditure_date = date_agg_format(expenditure_date)
        aggregate_start_date, aggregate_end_date = find_aggregate_date(
            form_type, expenditure_date
        )
        transactions_list = list_all_transactions_entity_lb(
            aggregate_start_date,
            aggregate_end_date,
            entity_id,
            cmte_id,
            levin_account_id,
        )
        if not transactions_list:
            return
        aggregate_amount = 0
        line_number = None
        itemized_ind = None
        for transaction in transactions_list:
            if transaction[5] != "Y":
                if not transaction[9] == "N":
                    aggregate_amount += transaction[0]
                if transaction[8] != "LEVIN_OTH_DISB":
                    itemized_ind = "I"
                else:
                    if aggregate_amount <= 200:
                        itemized_ind = "U"
                    else:
                        itemized_ind = "I"

                # if transaction[7] != None or (
                #     transaction[7] == None and transaction[6] != "X"
                # ):
                # aggregate_amount += transaction[0]
                if expenditure_date <= transaction[4]:
                    transaction_id = transaction[1]
                    put_sql_agg_amount_LB(
                        cmte_id,
                        transaction_id,
                        aggregate_amount,
                        itemized_ind
                    )

                    # child_SA_transaction_list = get_list_agg_child_schedA(report_id, cmte_id, transaction[1])
                    # for child_SA_transaction in child_SA_transaction_list:
                    #     put_sql_agg_amount_schedA(cmte_id, child_SA_transaction.get('transaction_id'), aggregate_amount)
                # #Updating aggregate amount to child auto generate sched B transactions
                # if child_flag_SB:
                #     child_SB_transaction_list = get_list_child_transactionId_schedB(cmte_id, transaction[1])
                #     for child_SB_transaction in child_SB_transaction_list:
                #         put_sql_agg_amount_schedB(cmte_id, child_SB_transaction[0], aggregate_amount)

    except Exception as e:
        raise Exception(
            "The update_aggregate_lb function is throwing an error: " + str(e)
        )


def superceded_report_id_list(report_id):
    try:
        report_list = []
        report_list.append(str(report_id))
        reportId = []
        # print(report_list)
        while True:
            # print('in loop')
            with connection.cursor() as cursor:
                query_string = """SELECT previous_report_id FROM public.reports WHERE report_id = %s AND form_type = 'F3X' AND delete_ind is distinct FROM 'Y' """
                cursor.execute(query_string, [report_id])
                reportId = cursor.fetchone()
            # print(reportId)
            if reportId is None:
                break
            elif reportId[0] is None:
                break
            else:
                report_list.append(str(reportId[0]))
                report_id = reportId[0]
        # print(report_list)
        return report_list
    except Exception as e:
        raise


def get_list_agg_child_schedA(report_id, cmte_id, transaction_id):
    """
    load all child sched_a items for this transaction
    """
    try:
        report_list = superceded_report_id_list(report_id)
        with connection.cursor() as cursor:

            # GET child rows from schedA table
            query_string = """SELECT cmte_id, report_id, line_number, transaction_type, transaction_id, back_ref_transaction_id, back_ref_sched_name, entity_id, 
            contribution_date, contribution_amount, aggregate_amt AS "contribution_aggregate", purpose_description, memo_code, memo_text, election_code, 
            election_other_description, create_date, donor_cmte_id, donor_cmte_name, transaction_type_identifier, levin_account_id, itemized_ind
                            FROM public.sched_a WHERE report_id in ('{}') AND cmte_id = %s AND back_ref_transaction_id = %s AND 
                            delete_ind is distinct from 'Y'""".format(
                "', '".join(report_list)
            )

            cursor.execute(
                """SELECT json_agg(t) FROM (""" + query_string + """) t""",
                [cmte_id, transaction_id],
            )

            for row in cursor.fetchall():
                # forms_obj.append(data_row)
                data_row = list(row)
                schedA_list = data_row[0]
            merged_list = []
            if not (schedA_list is None):
                for dictA in schedA_list:
                    entity_id = dictA.get("entity_id")
                    data = {"entity_id": entity_id, "cmte_id": cmte_id}
                    entity_list = get_entities(data)
                    dictEntity = entity_list[0]
                    merged_dict = {**dictA, **dictEntity}
                    merged_list.append(merged_dict)
        return merged_list
    except Exception:
        raise


def find_aggregate_date(form_type, contribution_date):
    """
    calculate aggregate start, end dates
    # TODO: do we need checking form_type here.
    """
    try:
        aggregate_start_date = None
        if form_type in ["F3X", "F24"]:
            year = contribution_date.year
            aggregate_start_date = datetime.date(year, 1, 1)
            aggregate_end_date = datetime.date(year, 12, 31)
        return aggregate_start_date, aggregate_end_date
    except Exception as e:
        raise Exception(
            "The aggregate_start_date function is throwing an error: " + str(e)
        )


def get_transactions_election_and_office(start_date, end_date, data, form_type='F3X'):
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
                e.transaction_id, 
                e.expenditure_amount as transaction_amt,
                COALESCE(e.dissemination_date, e.disbursement_date) as transaction_dt,
                e.aggregation_ind
        FROM public.sched_e e
        LEFT JOIN public.reports r ON r.report_id = e.report_id
        WHERE  
            e.cmte_id = %s
            AND COALESCE(e.dissemination_date, e.disbursement_date) >= %s
            AND COALESCE(e.dissemination_date, e.disbursement_date) <= %s
            AND e.election_code = %s
            AND e.delete_ind is distinct FROM 'Y'
            AND e.memo_code is null 
            AND r.form_type = %s
            ORDER BY transaction_dt ASC, e.create_date ASC;
        """
        _params = (data.get("cmte_id"), start_date, end_date, data.get("election_code"), form_type)
    elif cand_office == "S" or (cand_office == "H" and data.get("so_cand_state") in ['AK', 'DE', 'MT', 'ND', 'SD', 'VT', 'WY']):
        _sql = """
        SELECT  
                e.transaction_id, 
                e.expenditure_amount as transaction_amt,
                COALESCE(e.dissemination_date, e.disbursement_date) as transaction_dt,
                e.aggregation_ind
        FROM public.sched_e e
        LEFT JOIN public.reports r ON r.report_id = e.report_id
        WHERE  
            e.cmte_id = %s
            AND COALESCE(e.dissemination_date, e.disbursement_date) >= %s
            AND COALESCE(e.dissemination_date, e.disbursement_date) <= %s
            AND e.election_code = %s
            AND e.so_cand_state = %s
            AND e.delete_ind is distinct FROM 'Y' 
            AND e.memo_code is null
            AND r.form_type = %s
            ORDER BY transaction_dt ASC, e.create_date ASC; 
        """
        _params = (
            data.get("cmte_id"),
            start_date,
            end_date,
            data.get("election_code"),
            data.get("so_cand_state"),
            form_type
        )
    elif cand_office == "H" and data.get("so_cand_state") not in ['AK', 'DE', 'MT', 'ND', 'SD', 'VT', 'WY']:
        _sql = """
        SELECT  
                e.transaction_id, 
                e.expenditure_amount as transaction_amt,
                COALESCE(e.dissemination_date, e.disbursement_date) as transaction_dt,
                e.aggregation_ind
        FROM public.sched_e e
        LEFT JOIN public.reports r ON r.report_id = e.report_id
        WHERE  
            e.cmte_id = %s
            AND COALESCE(e.dissemination_date, e.disbursement_date) >= %s
            AND COALESCE(e.dissemination_date, e.disbursement_date) <= %s
            AND e.election_code = %s
            AND e.so_cand_state = %s
            AND e.so_cand_district = %s
            AND e.delete_ind is distinct FROM 'Y' 
            AND e.memo_code is null
            AND r.form_type = %s
            ORDER BY transaction_dt ASC, e.create_date ASC;  
        """
        _params = (
            data.get("cmte_id"),
            start_date,
            end_date,
            data.get("election_code"),
            data.get("so_cand_state"),
            data.get("so_cand_district"),
            form_type
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


def update_aggregate_se(data):
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
            trans_dt = date_agg_format(data.get("dissemination_date"))
        else:
            trans_dt = date_agg_format(data.get("disbursement_date"))

        # if isinstance(contribution_date, str):
        # contribution_date = date_agg_format(contribution_date)
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
            aggregate_start_date, aggregate_end_date, data, form_type
        )
        if not transaction_list:
            logger.debug("no SE transctions found.")
            return
        aggregate_amount = 0
        for transaction in transaction_list:
            # update aggregate amount for non-memo and dangled memo transactions
            # TODO: need to confirm dangled memo transaction is counted or not
            # if transaction["transaction_type_identifier"].endswith("_MEMO"):
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


def load_schedE(cmte_id, report_id, transaction_id):
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
            create_date, 
            last_update_date,
            mirror_transaction_id,
            mirror_report_id
            FROM public.sched_e
            WHERE cmte_id = %s
            AND report_id = %s
            AND transaction_id = %s) t 
            """
            # if is_back_ref:
            #     _sql = _sql + """ AND back_ref_transaction_id = %s) t"""
            # else:
            #     _sql = _sql + """ AND transaction_id = %s) t"""
            cursor.execute(_sql, (cmte_id, report_id, transaction_id))
            schedE_list = cursor.fetchone()[0]
            if schedE_list is None:
                raise Exception(
                    "No sched_e transaction found for transaction_id {}".format(
                        transaction_id
                    )
                )
            return schedE_list
        #     merged_list = []
        #     if schedE_list:
        #         for dictE in schedE_list:
        #             merged_list.append(dictE)
        # return merged_list
    except Exception:
        raise


def get_election_year(office_sought, election_state, election_district):
    try:
        if office_sought == "P":
            param_string = "&office_sought={}".format(office_sought)
            add_year = 4
        elif office_sought == "S":
            param_string = "&office_sought={}&election_state={}".format(
                office_sought, election_state
            )
            add_year = 6
        elif office_sought == "H":
            param_string = "&office_sought={}&election_state={}&election_district={}".format(
                office_sought, election_state, election_district
            )
            add_year = 2
        else:
            raise Exception("office_sought can only take P,S,H values")
        i = 1
        results = []
        election_year_list = []
        while True:
            ab = requests.get(
                "https://api.open.fec.gov/v1/election-dates/?sort=-election_date&api_key=50nTHLLMcu3XSSzLnB0hax2Jg5LFniladU5Yf25j&page={}&per_page=100&sort_hide_null=false&sort_nulls_last=false{}".format(
                    i, param_string
                )
            )
            results = results + ab.json()["results"]
            if (
                i == ab.json()["pagination"]["pages"]
                or ab.json()["pagination"]["pages"] == 0
            ):
                break
            else:
                i += 1
        logger.debug("count of FEC election dates API:" + str(len(results)))
        for result in results:
            if result["election_year"] not in election_year_list:
                election_year_list.append(result["election_year"])
        if election_year_list:
            election_year_list.sort(reverse=True)
            if election_year_list[0] + add_year >= datetime.datetime.now().year:
                election_year_list.insert(0, election_year_list[0] + add_year)
        return election_year_list
    except Exception as e:
        logger.debug(e)
        raise Exception(
            "The get_election_year function is throwing an error: " + str(e)
        )


def agg_dates(cmte_id, beneficiary_cand_id, expenditure_date):
    try:
        start_date = None
        end_date = None
        with connection.cursor() as cursor:
            cursor.execute(
                """SELECT json_agg(t) FROM (SELECT e.cand_office, e.cand_office_state, e.cand_office_district FROM public.entity e 
                WHERE e.cmte_id in ('C00000000') 
                AND substr(e.ref_cand_cmte_id,1,1) != 'C' AND e.ref_cand_cmte_id = %s AND e.delete_ind is distinct from 'Y') as t""",
                [beneficiary_cand_id],
            )
            # print(cursor.query)
            cand = cursor.fetchone()[0]
            logger.debug("Candidate Office Data: " + str(cand))
        if cand:
            cand = cand[0]
            if cand["cand_office"] == "H":
                add_year = 1
                if not (cand["cand_office_state"] and cand["cand_office_district"]):
                    raise Exception(
                        "The candidate details for candidate Id: {} are missing: office state and district".format(
                            beneficiary_cand_id
                        )
                    )
            elif cand["cand_office"] == "S":
                add_year = 5
                if not cand["cand_office_state"]:
                    raise Exception(
                        "The candidate details for candidate Id: {} are missing: office state".format(
                            beneficiary_cand_id
                        )
                    )
                cand["cand_office_district"] = None
            elif cand["cand_office"] == "P":
                add_year = 3
                cand["cand_office_state"] = None
                cand["cand_office_district"] = None
            else:
                raise Exception(
                    "The candidate id: {} does not belong to either Senate, House or Presidential office. Kindly check cand_office in entity table for details".format(
                        beneficiary_cand_id
                    )
                )
        else:
            raise Exception(
                "The candidate Id: {} is not present in the entity table.".format(
                    beneficiary_cand_id
                )
            )
        election_year_list = get_election_year(
            cand["cand_office"], cand["cand_office_state"], cand["cand_office_district"]
        )
        logger.debug("Election years based on FEC API:" + str(election_year_list))
        expenditure_year = (
            datetime.datetime.strptime(expenditure_date, "%m/%d/%Y").date().year
        )
        if len(election_year_list) >= 2:
            for i, val in enumerate(election_year_list):
                if i == len(election_year_list) - 2:
                    break
                if (
                    election_year_list[i + 1] < expenditure_year
                    and expenditure_year <= election_year_list[i]
                ):
                    end_date = datetime.date(election_year_list[i], 12, 31)
                    start_year = election_year_list[i] - add_year
                    start_date = datetime.date(start_year, 1, 1)
        if not end_date:
            if datetime.datetime.now().year % 2 == 1:
                end_year = datetime.datetime.now().year + add_year
                end_date = datetime.date(end_year, 12, 31)
                start_date = datetime.date(datetime.datetime.now().year, 1, 1)
            else:
                end_date = datetime.date(datetime.datetime.now().year, 12, 31)
                start_year = datetime.datetime.now().year - add_year
                start_date = datetime.date(start_year, 1, 1)
        return start_date, end_date
    except Exception as e:
        logger.debug(e)
        raise Exception("The agg_dates function is throwing an error: " + str(e))


def get_SF_transactions_candidate(start_date, end_date, beneficiary_cand_id):
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """SELECT json_agg(t) FROM (SELECT t1.transaction_id, t1.expenditure_date, t1.expenditure_amount, 
                t1.aggregate_general_elec_exp, t1.memo_code FROM public.sched_f t1 WHERE t1.payee_cand_id = %s AND t1.expenditure_date >= %s AND 
                t1.expenditure_date <= %s AND t1.delete_ind is distinct FROM 'Y' 
                AND (SELECT t2.delete_ind FROM public.reports t2 WHERE t2.report_id = t1.report_id) is distinct FROM 'Y'
                ORDER BY t1.expenditure_date ASC, t1.create_date ASC) t""",
                [beneficiary_cand_id, start_date, end_date],
            )
            if cursor.rowcount == 0:
                transaction_list = []
            else:
                transaction_list = cursor.fetchall()[0][0]
        logger.debug(transaction_list)
        return transaction_list
    except Exception as e:
        logger.debug(e)
        raise Exception(
            "The get_SF_transactions_candidate function is throwing an error: " + str(e)
        )


def update_aggregate_sf(cmte_id, beneficiary_cand_id, expenditure_date):
    try:
        aggregate_amount = 0.0
        # expenditure_date = datetime.datetime.strptime(expenditure_date, '%Y-%m-%d').date()
        cvg_start_date, cvg_end_date = agg_dates(
            cmte_id, beneficiary_cand_id, expenditure_date
        )
        transaction_list = get_SF_transactions_candidate(
            cvg_start_date, cvg_end_date, beneficiary_cand_id
        )
        if transaction_list:
            for transaction in transaction_list:
                if transaction["memo_code"] != "X":
                    aggregate_amount += float(transaction["expenditure_amount"])
                if transaction["expenditure_date"] >= expenditure_date:
                    put_aggregate_SF(aggregate_amount, transaction["transaction_id"])
    except Exception as e:
        logger.debug(e)
        raise Exception(
            "The update_aggregate_general_elec_exp API is throwing an error: " + str(e)
        )


def put_aggregate_SF(aggregate_general_elec_exp, transaction_id):
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE public.sched_f SET aggregate_general_elec_exp = %s WHERE transaction_id = %s",
                [aggregate_general_elec_exp, transaction_id],
            )
            if cursor.rowcount == 0:
                raise Exception(
                    "The Transaction ID: {} does not exist in schedF table".format(
                        transaction_id
                    )
                )
    except Exception as e:
        logger.debug(e)
        raise Exception("The put_aggregate_SF function is throwing an error: " + str(e))


def load_schedF(cmte_id, report_id, transaction_id):
    try:
        with connection.cursor() as cursor:
            # GET single row from schedA table
            _sql = """SELECT json_agg(t) FROM ( SELECT
            sf.cmte_id,
            sf.report_id,
            sf.transaction_type_identifier,
            sf.transaction_id, 
            sf.back_ref_transaction_id,
            sf.back_ref_sched_name,
            sf.coordinated_exp_ind,
            sf.designating_cmte_id,
            sf.designating_cmte_name,
            sf.subordinate_cmte_id,
            sf.subordinate_cmte_name,
            sf.subordinate_cmte_street_1,
            sf.subordinate_cmte_street_2,
            sf.subordinate_cmte_city,
            sf.subordinate_cmte_state,
            sf.subordinate_cmte_zip,
            sf.payee_entity_id as entity_id,
            sf.expenditure_date,
            sf.expenditure_amount,
            sf.aggregate_general_elec_exp,
            sf.purpose,
            sf.category_code,
            sf.payee_cmte_id,
            sf.payee_cand_id as beneficiary_cand_id,
            sf.payee_cand_last_name as cand_last_name,
            sf.payee_cand_fist_name as cand_first_name,
            sf.payee_cand_middle_name as cand_middle_name,
            sf.payee_cand_prefix as cand_prefix,
            sf.payee_cand_suffix as cand_suffix,
            sf.payee_cand_office as cand_office,
            sf.payee_cand_state as cand_office_state,
            sf.payee_cand_district as cand_office_district,
            sf.memo_code,
            sf.memo_text,
            sf.delete_ind,
            sf.create_date,
            sf.last_update_date,
            (SELECT DISTINCT ON (e.ref_cand_cmte_id) e.entity_id 
            FROM public.entity e WHERE e.entity_id not in (select ex.entity_id from excluded_entity ex where ex.cmte_id = sf.cmte_id) 
                        AND substr(e.ref_cand_cmte_id,1,1) != 'C' AND e.ref_cand_cmte_id = sf.payee_cand_id AND e.delete_ind is distinct from 'Y'
                        ORDER BY e.ref_cand_cmte_id DESC, e.entity_id DESC) AS beneficiary_cand_entity_id
            FROM public.sched_f sf
            WHERE sf.report_id = %s AND sf.cmte_id = %s AND sf.transaction_id = %s
            ) t
            """
            cursor.execute(_sql, (report_id, cmte_id, transaction_id))
            schedF_list = cursor.fetchone()[0]
            if schedF_list is None:
                raise Exception(
                    "No sched_f transaction found for transaction_id {}".format(
                        transaction_id
                    )
                )
            return schedF_list
            # merged_list = []
        #     for dictF in schedF_list:
        #         entity_id = dictF.get("entity_id")
        #         data = {"entity_id": entity_id, "cmte_id": cmte_id}
        #         entity_list = get_entities(data)
        #         dictEntity = entity_list[0]
        #         del dictEntity["cand_office"]
        #         del dictEntity["cand_office_state"]
        #         del dictEntity["cand_office_district"]
        #         merged_dict = {**dictF, **dictEntity}
        #         merged_list.append(merged_dict)
        # return merged_list
    except Exception:
        raise


def load_schedH6(cmte_id, report_id, transaction_id):
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
            create_date,
            last_update_date
            FROM public.sched_h6
            WHERE report_id = %s AND cmte_id = %s AND transaction_id = %s
            ) t
            """
            cursor.execute(_sql, (report_id, cmte_id, transaction_id))
            schedH6_list = cursor.fetchone()[0]
            if schedH6_list is None:
                raise Exception(
                    "No sched_H6 transaction found for transaction_id {}".format(
                        transaction_id
                    )
                )
            return schedH6_list
        #     merged_list = []
        #     for tran in schedH6_list:
        #         entity_id = tran.get("entity_id")
        #         q_data = {"entity_id": entity_id, "cmte_id": cmte_id}
        #         dictEntity = get_entities(q_data)[0]
        #         merged_list.append({**tran, **dictEntity})
        # return merged_list
    except Exception:
        raise


def load_schedH4(cmte_id, report_id, transaction_id):
    try:
        logger.debug(
            "loading h4 item with cmte_id {}, report_id {}, transaction_id {}".format(
                cmte_id, report_id, transaction_id
            )
        )
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
            create_date,
            last_update_date
            FROM public.sched_h4
            WHERE report_id = %s AND cmte_id = %s AND transaction_id = %s
            ) t
            """
            cursor.execute(_sql, (report_id, cmte_id, transaction_id))
            tran_list = cursor.fetchone()[0]
            if not tran_list:
                raise Exception(
                    "No sched_H4 transaction found for transaction_id {}".format(
                        transaction_id
                    )
                )
        #     merged_list = []
        #     for tran in tran_list:
        #         entity_id = tran.get("payee_entity_id")
        #         q_data = {"entity_id": entity_id, "cmte_id": cmte_id}
        #         dictEntity = get_entities(q_data)[0]
        #         merged_list.append({**tran, **dictEntity})
        # return merged_list[0]
        return tran_list
    except Exception:
        raise


def update_activity_event_amount_ytd_h4(data):
    """
    aggregate and update 'activity_event_amount_ytd' for all h4 transactions
    if event_identifier is provided, will do event-based aggregation;
    else will do event_type-based aggregation
    """
    try:

        logger.debug("updating ytd amount:")
        # make sure transaction list comes back sorted by contribution_date ASC
        expenditure_dt = date_agg_format(data.get("expenditure_date"))
        aggregate_start_date = datetime.date(expenditure_dt.year, 1, 1)
        aggregate_end_date = datetime.date(expenditure_dt.year, 12, 31)
        if data.get("activity_event_identifier"):
            transactions_list = list_all_transactions_event_identifier_h4(
                aggregate_start_date,
                aggregate_end_date,
                data.get("activity_event_identifier"),
                data.get("cmte_id"),
            )
        else:
            transactions_list = list_all_transactions_event_type_h4(
                aggregate_start_date,
                aggregate_end_date,
                data.get("activity_event_type"),
                data.get("cmte_id"),
            )
        aggregate_amount = 0
        for transaction in transactions_list:
            aggregate_amount += transaction[0]
            transaction_id = transaction[1]
            update_transaction_ytd_amount_h4(
                data.get("cmte_id"), transaction_id, aggregate_amount
            )

    except Exception as e:
        raise Exception(
            "The update_activity_event_amount_ytd function is throwing an error: "
            + str(e)
        )


def list_all_transactions_event_type_h4(start_dt, end_dt, activity_event_type, cmte_id):
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
                t1.transaction_id
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


def update_transaction_ytd_amount_h4(cmte_id, transaction_id, aggregate_amount):
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


def list_all_transactions_event_identifier_h4(
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
                t1.transaction_id
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


def is_pac(cmte_id):
    _sql = """
    SELECT cmte_type_category
    FROM committee_master
    WHERE cmte_id = %s;
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(_sql, [cmte_id])
            if cursor.rowcount > 0:
                return cursor.fetchone()[0] == "PAC"
        return False
    except:
        raise


def update_activity_event_amount_ytd_h6(data):
    """
    aggregate and update 'activity_event_amount_ytd' for all h6 transactions
    """
    try:

        logger.debug("updating ytd amount h6:")
        # make sure transaction list comes back sorted by contribution_date ASC
        expenditure_dt = date_agg_format(data.get("expenditure_date"))
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
                t1.transaction_id
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


def update_linenumber_aggamt_transactions_SA(
    contribution_date, transaction_type_identifier, entity_id, cmte_id, report_id
):
    """
    helper function for updating private contribution line number based on aggrgate amount
    the aggregate amount is a contribution_date-based on incremental update, the line number
    is updated accordingly:
    edit 1: check if the report corresponding to the transaction is deleted or not (delete_ind flag in reports table) 
            and only when it is NOT add contribution_amount to aggregate amount
    edit 2: updation of aggregate amount will roll to all transacctions irrespective of report id and report being filed
    edit 3: if back_ref_transaction_id is none, then check if memo_code is NOT 'X' and if it is not, add contribution_amount to aggregate amount; 
            if back_ref_transaction_id is NOT none, then add irrespective of memo_code, add contribution_amount to aggregate amount
    e.g.
    date, contribution_amount, aggregate_amount, line_number
    1/1/2018, 50, 50, 11AII
    2/1/2018, 60, 110, 11AII
    3/1/2018, 100, 210, 11AI (aggregate_amount > 200, update line number)

    """
    try:
        if transaction_type_identifier not in ('IND_BNDLR', 'REG_ORG_BNDLR'):
            child_flag_SB = False
            child_flag_SA = False
            itemization_value = 200
            # itemized_transaction_list = []
            # unitemized_transaction_list = []
            form_type = find_form_type(report_id, cmte_id)
            if isinstance(contribution_date, str):
                contribution_date = date_agg_format(contribution_date)
            aggregate_start_date, aggregate_end_date = find_aggregate_date(
                form_type, contribution_date
            )
            # checking for child tranaction identifer for updating auto generated SB transactions
            if (
                transaction_type_identifier
                in AUTO_GENERATE_SCHEDB_PARENT_CHILD_TRANSTYPE_DICT
            ):
                child_flag_SB = True
                child_transaction_type_identifier = AUTO_GENERATE_SCHEDB_PARENT_CHILD_TRANSTYPE_DICT.get(
                    transaction_type_identifier
                )
            # checking for child tranaction identifer for updating auto generated SA transactions
            if (
                transaction_type_identifier
                in AUTO_GENERATE_SCHEDA_PARENT_CHILD_TRANSTYPE_DICT
            ):
                child_flag_SA = True
                child_transaction_type_identifier = AUTO_GENERATE_SCHEDA_PARENT_CHILD_TRANSTYPE_DICT.get(
                    transaction_type_identifier
                )
            # make sure transaction list comes back sorted by contribution_date ASC
            transactions_list = list_all_transactions_entity(
                aggregate_start_date, aggregate_end_date, entity_id, cmte_id
            )
            aggregate_amount = 0
            PAC_aggregate_amount = 0
            HQ_aggregate_amount = 0
            CO_aggregate_amount = 0
            NPRE_aggregate_amount = 0
            RE_aggregate_amount = 0
            REMAIN_aggregate_amount = 0
            committee_type = cmte_type(cmte_id)
            for transaction in transactions_list:
                # checking in reports table if the delete_ind flag is false for the corresponding report
                if transaction[5] != "Y":
                    # checking if the back_ref_transaction_id is null or not.
                    # If back_ref_transaction_id is none, checking if the transaction is a memo or not, using memo_code not equal to X.
                    if (
                        transaction[7] != None
                        or (
                            transaction[7] == None
                            and (
                                # transaction[6] != "X" or
                                # (transaction[9] == "A" and transaction[0] < 0)
                                # or transaction[9] == "R"
                                not (
                                    transaction[6] == "X"
                                    and transaction[9] == "A"
                                    and transaction[0] > 0
                                )
                            )
                        )
                    ) and transaction[10] != "N":
                        if (committee_type == "PAC") and transaction[
                            8
                        ] in PAC_AGGREGATE_TYPES_1:
                            PAC_aggregate_amount += transaction[0]
                            aggregate_amount = PAC_aggregate_amount
                        elif (committee_type == "PTY") and transaction[
                            8
                        ] in PTY_AGGREGATE_TYPES_HQ:
                            if transaction[8] in [
                                "OPEXP_HQ_ACC_REG_REF",
                                "OPEXP_HQ_ACC_IND_REF",
                                "OPEXP_HQ_ACC_TRIB_REF",
                            ]:
                                HQ_aggregate_amount -= transaction[0]
                            else:
                                HQ_aggregate_amount += transaction[0]
                            aggregate_amount = HQ_aggregate_amount
                        elif (committee_type == "PTY") and transaction[
                            8
                        ] in PTY_AGGREGATE_TYPES_CO:
                            if transaction[8] in [
                                "OPEXP_CONV_ACC_REG_REF",
                                "OPEXP_CONV_ACC_TRIB_REF",
                                "OPEXP_CONV_ACC_IND_REF",
                            ]:
                                CO_aggregate_amount -= transaction[0]
                            else:
                                CO_aggregate_amount += transaction[0]
                            aggregate_amount = CO_aggregate_amount
                        elif (committee_type == "PTY") and transaction[
                            8
                        ] in PTY_AGGREGATE_TYPES_NPRE:
                            if transaction[8] in [
                                "OTH_DISB_NP_RECNT_REG_REF",
                                "OTH_DISB_NP_RECNT_TRIB_REF",
                                "OTH_DISB_NP_RECNT_IND_REF",
                            ]:
                                NPRE_aggregate_amount -= transaction[0]
                            else:
                                NPRE_aggregate_amount += transaction[0]
                            aggregate_amount = NPRE_aggregate_amount
                        elif (committee_type == "PTY") and transaction[
                            8
                        ] in PTY_AGGREGATE_TYPES_RE:
                            RE_aggregate_amount += transaction[0]
                            aggregate_amount = RE_aggregate_amount
                        else:
                            if transaction[8] != "CON_EAR_DEP":
                                REMAIN_aggregate_amount += transaction[0]
                            aggregate_amount = REMAIN_aggregate_amount
                    # Removed report_id constraint as we have to modify aggregate amount irrespective of report_id
                    # if str(report_id) == str(transaction[2]):
                    if contribution_date <= transaction[4] and transaction[8] not in [
                        "OPEXP_HQ_ACC_REG_REF",
                        "OPEXP_HQ_ACC_IND_REF",
                        "OPEXP_HQ_ACC_TRIB_REF",
                        "OPEXP_CONV_ACC_REG_REF",
                        "OPEXP_CONV_ACC_TRIB_REF",
                        "OPEXP_CONV_ACC_IND_REF",
                        "OTH_DISB_NP_RECNT_REG_REF",
                        "OTH_DISB_NP_RECNT_TRIB_REF",
                        "OTH_DISB_NP_RECNT_IND_REF",
                    ]:

                        line_number, itemized_ind = get_linenumber_itemization(
                            transaction[8],
                            aggregate_amount,
                            itemization_value,
                            transaction[3],
                        )
                        if not transaction[11] in ["FU", "FI"]:  # if not forced
                            put_sql_linenumber_schedA(
                                cmte_id,
                                line_number,
                                itemized_ind,
                                transaction[1],
                                entity_id,
                                aggregate_amount,
                            )
                        else:
                            put_sql_linenumber_schedA(
                                cmte_id,
                                line_number,
                                transaction[11],
                                transaction[1],
                                entity_id,
                                aggregate_amount,
                            )

                    # Updating aggregate amount to child auto generate sched A transactions
                    if child_flag_SA:
                        child_SA_transaction_list = get_list_agg_child_schedA(
                            report_id, cmte_id, transaction[1]
                        )
                        for child_SA_transaction in child_SA_transaction_list:
                            put_sql_agg_amount_schedA(
                                cmte_id,
                                child_SA_transaction.get("transaction_id"),
                                aggregate_amount
                            )
                    # Updating aggregate amount to child auto generate sched B transactions
                    if child_flag_SB:
                        child_SB_transaction_list = get_list_child_transactionId_schedB(
                            cmte_id, transaction[1]
                        )
                        for child_SB_transaction in child_SB_transaction_list:
                            put_sql_agg_amount_schedB(
                                cmte_id, child_SB_transaction[0], aggregate_amount
                            )

    except Exception as e:
        raise Exception(
            "The update_linenumber_aggamt_transactions_SA function is throwing an error: "
            + str(e)
        )


def list_all_transactions_entity(
    aggregate_start_date, aggregate_end_date, entity_id, cmte_id
):
    """
    load all transactions for an entity within a time window
    return value: a list of transction_records [
       (contribution_amount, transaction_id, report_id, line_number, contribution_date),
       ....
    ]
    return items are sorted by contribution_date in ASC order
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
            (SELECT t1.contribution_amount, 
                t1.transaction_id, 
                t1.report_id, 
                t1.line_number, 
                t1.contribution_date as transaction_date, 
                (SELECT t2.delete_ind FROM public.reports t2 WHERE t2.report_id = t1.report_id), 
                t1.memo_code, 
                t1.back_ref_transaction_id,
                t1.transaction_type_identifier,
                t1.reattribution_ind,
                t1.aggregation_ind,
                t1.itemized_ind,
                t1.create_date
            FROM public.sched_a t1 
            WHERE entity_id = %s 
            AND cmte_id = %s 
            AND contribution_date >= %s 
            AND contribution_date <= %s 
            AND delete_ind is distinct FROM 'Y'
            UNION ALL
            SELECT t1.expenditure_amount, 
                t1.transaction_id, 
                t1.report_id, 
                t1.line_number, 
                t1.expenditure_date as transaction_date, 
                (SELECT t2.delete_ind FROM public.reports t2 WHERE t2.report_id = t1.report_id),t1.memo_code, 
                t1.back_ref_transaction_id,
                t1.transaction_type_identifier,
                null as reattribution_ind,
                null as aggregation_ind,
                t1.itemized_ind,
                t1.create_date
            FROM public.sched_b t1
            WHERE entity_id = %s 
            AND cmte_id = %s 
            AND expenditure_date >= %s 
            AND expenditure_date <= %s 
            AND transaction_type_identifier in ('OPEXP_HQ_ACC_REG_REF',
                                                'OPEXP_HQ_ACC_IND_REF',
                                                'OPEXP_HQ_ACC_TRIB_REF',
                                                'OPEXP_CONV_ACC_REG_REF',
                                                'OPEXP_CONV_ACC_TRIB_REF',
                                                'OPEXP_CONV_ACC_IND_REF',
                                                'OTH_DISB_NP_RECNT_REG_REF',
                                                'OTH_DISB_NP_RECNT_TRIB_REF',
                                                'OTH_DISB_NP_RECNT_IND_REF')
            AND delete_ind is distinct FROM 'Y'
            ) 
            ORDER BY transaction_date ASC, create_date ASC
            """,
                [
                    entity_id,
                    cmte_id,
                    aggregate_start_date,
                    aggregate_end_date,
                    entity_id,
                    cmte_id,
                    aggregate_start_date,
                    aggregate_end_date,
                ],
            )
            # print(cursor.query)
            transactions_list = cursor.fetchall()
        return transactions_list
    except Exception as e:
        raise Exception(
            "The list_all_transactions_entity function is throwing an error: " + str(e)
        )


@update_F3X
def update_sa_itmization_status(data, item_status=None):
    """
    helpder function for force itemization
    """
    transaction_type_identifier = data.get("transaction_type_identifier")
    transaction_id = data.get("transaction_id")
    report_id = data.get("report_id")
    if transaction_type_identifier in ITEMIZATION_TRANSACTION_TYPE_IDENTIFIER_LIST:

        line_number = "11AI" if item_status == "FI" else "11AII"

        _sql = """
        update public.sched_a
        set itemized_ind = %s, line_number = %s
        where transaction_id = %s and report_id = %s
        """
        parameters = [item_status, line_number, transaction_id, report_id]
    else:
        _sql = """
        update public.sched_a
        set itemized_ind = %s
        where transaction_id = %s and report_id = %s
        """
        parameters = [item_status, transaction_id, report_id]
    with connection.cursor() as cursor:
        cursor.execute(_sql, parameters)
        if cursor.rowcount == 0:
            raise Exception(
                "update itemization status failed for {}".format(transaction_id)
            )
    return data


def get_linenumber_itemization(
    transaction_type_identifier, aggregate_amount, itemization_value, line_number
):
    try:
        itemized_ind = None
        output_line_number = None
        if transaction_type_identifier in ITEMIZATION_TRANSACTION_TYPE_IDENTIFIER_LIST:
            if aggregate_amount <= itemization_value:
                output_line_number = "11AII"
            else:
                output_line_number = "11AI"
        else:
            output_line_number = line_number

        if (
            transaction_type_identifier
            in ITEMIZED_IND_UPDATE_TRANSACTION_TYPE_IDENTIFIER
            and aggregate_amount <= itemization_value
        ):
            itemized_ind = "U"
        else:
            itemized_ind = "I"
        return output_line_number, itemized_ind
    except Exception as e:
        raise Exception(
            "The get_linenumber_itemization function is throwing an error: " + str(e)
        )


def put_sql_linenumber_schedA(
    cmte_id, line_number, itemized_ind, transaction_id, entity_id, aggregate_amount
):
    """
    update line number
    """
    try:
        with connection.cursor() as cursor:
            # Insert data into schedA table
            cursor.execute(
                """UPDATE public.sched_a SET line_number = %s, itemized_ind = %s, aggregate_amt = %s WHERE transaction_id = %s AND cmte_id = %s AND entity_id = %s AND delete_ind is distinct from 'Y'""",
                [
                    line_number,
                    itemized_ind,
                    aggregate_amount,
                    transaction_id,
                    cmte_id,
                    entity_id,
                ],
            )
            # print(cursor.query)
            if cursor.rowcount == 0:
                raise Exception(
                    "put_sql_linenumber_schedA function: The Transaction ID: {} does not exist in schedA table".format(
                        transaction_id
                    )
                )
    except Exception:
        raise


def get_list_child_transactionId_schedB(cmte_id, transaction_id):
    """
    get all children sched_b items:
    back_ref_transaction_id == transaction_id
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """SELECT transaction_id
                FROM public.sched_b 
                WHERE cmte_id = %s 
                AND back_ref_transaction_id = %s 
                AND delete_ind is distinct from 'Y'""",
                [cmte_id, transaction_id],
            )
            transactions_list = cursor.fetchall()
        return transactions_list
    except Exception as e:
        raise Exception(
            "The get_list_child_transactionId_schedB function is throwing an error: "
            + str(e)
        )


def put_sql_agg_amount_schedB(cmte_id, transaction_id, aggregate_amount):
    """
    update aggregate amount
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE public.sched_b 
                SET aggregate_amt = %s
                WHERE transaction_id = %s 
                AND cmte_id = %s 
                AND delete_ind is distinct from 'Y'
                """,
                [aggregate_amount, transaction_id, cmte_id],
            )
            if cursor.rowcount == 0:
                raise Exception(
                    "put_sql_agg_amount_schedB function: The Transaction ID: {} does not exist in schedB table".format(
                        transaction_id
                    )
                )
    except Exception:
        raise


def put_sql_agg_amount_LB(
    cmte_id, transaction_id, aggregate_amount, itemized_ind
):
    """
    update aggregate amount
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE public.sched_b 
                SET aggregate_amt = %s,
                    itemized_ind = %s
                WHERE transaction_id = %s 
                AND cmte_id = %s 
                AND delete_ind is distinct from 'Y'
                """,
                [aggregate_amount, itemized_ind, transaction_id, cmte_id],
            )
            if cursor.rowcount == 0:
                raise Exception(
                    "put_sql_agg_amount_LB function: The Transaction ID: {} does not exist in schedB table".format(
                        transaction_id
                    )
                )
    except Exception:
        raise


def func_aggregate_amount(
    contribution_date, transaction_type_identifier, entity_id, cmte_id
):
    """
    query aggregate amount based on start/end date, transaction_type, entity_id and cmte_id
    """
    try:
        with connection.cursor() as cursor:

            if transaction_type_identifier in PTY_AGGREGATE_TYPES_HQ:
                params = """ AND transaction_type_identifier IN ('{}')""".format(
                    "', '".join(PTY_AGGREGATE_TYPES_HQ)
                )
            elif transaction_type_identifier in PTY_AGGREGATE_TYPES_CO:
                params = """ AND transaction_type_identifier IN ('{}')""".format(
                    "', '".join(PTY_AGGREGATE_TYPES_CO)
                )
            elif transaction_type_identifier in PTY_AGGREGATE_TYPES_NPRE:
                params = """ AND transaction_type_identifier IN ('{}')""".format(
                    "', '".join(PTY_AGGREGATE_TYPES_NPRE)
                )
            elif transaction_type_identifier in PTY_AGGREGATE_TYPES_RE:
                params = """ AND transaction_type_identifier IN ('{}')""".format(
                    "', '".join(PTY_AGGREGATE_TYPES_RE)
                )
            elif transaction_type_identifier in PAC_AGGREGATE_TYPES_1:
                params = """ AND transaction_type_identifier IN ('{}')""".format(
                    "', '".join(PAC_AGGREGATE_TYPES_1)
                )
            else:
                params = """ AND transaction_type_identifier NOT IN ('{}')""".format(
                    "', '".join(
                        PAC_AGGREGATE_TYPES_1
                        + PTY_AGGREGATE_TYPES_HQ
                        + PTY_AGGREGATE_TYPES_CO
                        + PTY_AGGREGATE_TYPES_NPRE
                        + PTY_AGGREGATE_TYPES_RE
                    )
                )

            query_string = """SELECT aggregate_amt, contribution_date as transaction_date, create_date
                FROM sched_a  WHERE entity_id = %s {0} AND cmte_id = %s 
                AND extract('year' FROM contribution_date) = extract('year' FROM %s::date)
                AND contribution_date <= %s::date
                AND ((back_ref_transaction_id IS NULL 
                AND (memo_code IS NULL OR (reattribution_ind='A' AND contribution_amount<0) OR reattribution_ind='R')) 
                OR (back_ref_transaction_id IS NOT NULL))
                AND delete_ind is distinct FROM 'Y' 
                ORDER BY transaction_date DESC, create_date DESC;""".format(
                params
            )

            cursor.execute(
                query_string, [entity_id, cmte_id, contribution_date, contribution_date]
            )
            result = cursor.fetchone()
            if result:
                aggregate_amt = result[0]
                # Handling aggregate for few schedule B transactions as they are expected to be added to SA aggregate
                query_string_1 = """SELECT SUM(expenditure_amount)
                    FROM sched_b WHERE entity_id = %s {0} AND cmte_id = %s
                    AND extract('year' FROM expenditure_date) = extract('year' FROM %s::date)
                    AND expenditure_date <= %s::date
                    AND expenditure_date >= %s::date
                    AND back_ref_transaction_id IS NULL
                    AND delete_ind is distinct FROM 'Y'""".format(
                    params
                )
                cursor.execute(
                    query_string_1,
                    [
                        entity_id,
                        cmte_id,
                        contribution_date,
                        contribution_date,
                        result[1],
                    ],
                )
                SB_agg = cursor.fetchone()

            else:
                aggregate_amt = 0
                # Handling aggregate for few schedule B transactions as they are expected to be added to SA aggregate
                query_string_1 = """SELECT SUM(expenditure_amount)
                    FROM sched_b WHERE entity_id = %s {0} AND cmte_id = %s
                    AND extract('year' FROM expenditure_date) = extract('year' FROM %s::date)
                    AND expenditure_date <= %s::date
                    AND back_ref_transaction_id IS NULL
                    AND delete_ind is distinct FROM 'Y'""".format(
                    params
                )
                cursor.execute(
                    query_string_1,
                    [entity_id, cmte_id, contribution_date, contribution_date],
                )
                SB_agg = cursor.fetchone()

            if SB_agg and SB_agg[0]:
                aggregate_amt -= SB_agg[0]

        return aggregate_amt
    except Exception as e:
        raise Exception("The aggregate_amount function is throwing an error: " + str(e))
