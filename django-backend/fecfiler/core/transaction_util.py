import logging
from functools import lru_cache
from django.db import connection
from fecfiler.core.views import get_entities, NoOPError, superceded_report_id_list, cmte_type
import datetime

logger = logging.getLogger(__name__)


def validate_new_election_year(cmte_id, report_id):
    """
    helper function for checking a report a NEW election year:
    checking cvg_start_date month = 1 and day = 1 
    """

    _sql = """
    SELECT extract(day from cvg_start_date) as d, 
    extract(month from cvg_start_date) as m 
    FROM public.reports
    WHERE report_id = %s and cmte_id = %s
    and delete_ind is distinct from 'Y'
    """
    try:
        with connection.cursor() as cursor:
            # cursor.execute(count_sql, (report_id, cmte_id, report_id, cmte_id))
            # if cursor.rowcount == 0:
            cursor.execute(_sql, (report_id, cmte_id))
            if cursor.rowcount:
                _res = cursor.fetchone()
                if int(_res[0]) == 1 and int(_res[1] == 1):
                    logger.debug("new election year report identified.")
                    return True
        return False
    except:
        raise


def delete_child_transaction(table, cmte_id, transaction_id):
    """
    delete sql transaction
    """
    _sql1 = """UPDATE public.{}""".format(table)
    _sql2 = """ SET delete_ind = 'Y' 
            WHERE back_ref_transaction_id = %s AND cmte_id = %s
        """
    _v = (transaction_id, cmte_id)
    logger.debug("delete sql: {}".format(_sql1 + _sql2))
    do_transaction(_sql1 + _sql2, _v)


def restore_child_transaction(table, cmte_id, transaction_id):
    """
    restore sql transaction
    """
    _sql1 = """UPDATE public.{}""".format(table)
    _sql2 = """ SET delete_ind = '' 
            WHERE back_ref_transaction_id = %s AND cmte_id = %s
        """
    _v = (transaction_id, cmte_id)
    do_transaction(_sql1 + sql2, _v)


def update_sched_c_parent(cmte_id, transaction_id, new_payment, old_payment=0):
    """
    update parent sched_c transaction when a child payemnt transaction saved
    """
    logger.debug("update_sched_c_parent...")
    _sql1 = """
        SELECT loan_payment_to_date, loan_balance
        FROM public.sched_c 
        WHERE transaction_id = '{}'
        AND cmte_id = '{}'
        AND delete_ind is distinct from 'Y'
    """.format(
        transaction_id, cmte_id
    )

    _sql2 = """
            UPDATE public.sched_c
            SET loan_payment_to_date = %s,
                loan_balance = %s,
                last_update_date = %s
            WHERE transaction_id = %s 
            AND cmte_id = %s
            AND delete_ind is distinct from 'Y'
        """

    try:
        # new_beginning_balance = new_balance
        with connection.cursor() as cursor:
            cursor.execute(_sql1)

            # no child found anymore, return; propagation update done
            if cursor.rowcount == 0:
                logger.debug("parent not found")
                raise Exception("error: sched_c parent missing")
            data = cursor.fetchone()

            # beginning_balance = data[0]
            payment_amount = data[0]
            # take care of null value issue for new loan
            if not payment_amount:
                payment_amount = 0
            balance_at_close = data[1]
            logger.debug("loan current payment amt:{}".format(payment_amount))
            logger.debug("loan current payment amt:{}".format(balance_at_close))
            new_payment_amount = (
                float(payment_amount) + float(new_payment) - float(old_payment)
            )
            new_balance_at_close = (
                float(balance_at_close) - float(new_payment) + float(old_payment)
            )
        logger.debug(
            "update parent with new payment {}, new balance {}".format(
                new_payment_amount, new_balance_at_close
            )
        )
        _v = (
            new_payment_amount,
            new_balance_at_close,
            datetime.datetime.now(),
            transaction_id,
            cmte_id,
        )
        logger.debug("update sched_c with values: {}".format(_v))
        do_transaction(_sql2, _v)
        logger.debug("loan {} update successful.".format(transaction_id))
    except:
        raise


def update_sched_d_parent(cmte_id, transaction_id, new_payment, old_payment=0):
    """
    update parent sched_d transaction when a child payemnt transaction saved
    """
    logger.debug("update_sched_d_parent...")
    _sql1 = """
        SELECT payment_amount, balance_at_close
        FROM public.sched_d 
        WHERE transaction_id = '{}'
        AND cmte_id = '{}'
        AND delete_ind is distinct from 'Y'
    """.format(
        transaction_id, cmte_id
    )

    _sql2 = """
            UPDATE public.sched_d
            SET payment_amount = %s,
                balance_at_close = %s,
                last_update_date = %s
            WHERE transaction_id = %s 
            AND cmte_id = %s
            AND delete_ind is distinct from 'Y'
        """

    try:
        # new_beginning_balance = new_balance
        with connection.cursor() as cursor:
            cursor.execute(_sql1)

            # no child found anymore, return; propagation update done
            if cursor.rowcount == 0:
                logger.debug("parent not found")
                raise Exception("error: sched_d parent missing")
            data = cursor.fetchone()
            # beginning_balance = data[0]
            payment_amount = data[0]
            balance_at_close = data[1]
            new_payment_amount = (
                float(payment_amount) + float(new_payment) - float(old_payment)
            )
            new_balance_at_close = (
                float(balance_at_close) - float(new_payment) + float(old_payment)
            )
        logger.debug(
            "update parent with payment {}, close_b {}".format(
                new_payment_amount, new_balance_at_close
            )
        )
        _v = (
            new_payment_amount,
            new_balance_at_close,
            datetime.datetime.now(),
            transaction_id,
            cmte_id,
        )
        logger.debug("update sched_d with values: {}".format(_v))
        do_transaction(_sql2, _v)
        logger.debug("parent update successful.")
    except:
        raise


# def do_transction(sql, arg):


def do_transaction(sql, values):
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql, values)
            logger.debug("transaction done with rowcount:{}".format(cursor.rowcount))
            # if cursor.rowcount == 0:
            #     raise Exception("The sql transaction: {} failed...".format(sql))
    except Exception:
        raise


def update_earmark_parent_purpose(data):
    """
    for earmark transaction only:
    when an earmark child transaction is added or updated,
    the child entity_name should be updated in parent transaction 
    'purpose_description' field

    update: part of the description like 'Earmarked for' and 'Earmarked through'
    is defined in dynamic forms and we only need to update entity name here
    """
    desc_start = {
        # "EAR_REC_CONVEN_ACC_MEMO": "Earmarked for Convention Account ",
        # "EAR_REC_HQ_ACC_MEMO": "Earmarked for Headquarters Account ",
        # "EAR_REC_RECNT_ACC_MEMO": "Earmarked for Recount Account ",
    }
    parent_tran_id = data.get("back_ref_transaction_id")
    cmte_id = data.get("cmte_id")
    report_id = data.get("report_id")
    entity_name = data.get("entity_name")
    tran_type = data.get("transaction_type_identifier")
    # if tran_type in desc_start:
    #     purpose = desc_start.get(tran_type) + entity_name
    # else:
    #     purpose = entity_name
    purpose = entity_name
    _sql = """
    UPDATE public.sched_a 
    SET purpose_description = %s 
    WHERE transaction_id = %s AND report_id = %s AND cmte_id = %s 
    AND delete_ind is distinct from 'Y'
    """
    try:
        with connection.cursor() as cursor:
            # Insert data into schedA table
            logger.debug("update parent purpose with sql:{}".format(_sql))
            logger.debug(
                "update parent {} with purpose:{}".format(parent_tran_id, purpose)
            )
            # print(report_id, cmte_id)
            cursor.execute(_sql, [purpose, parent_tran_id, report_id, cmte_id])
            if cursor.rowcount == 0:
                raise Exception(
                    "update parent purpose failed for transaction {}".format(
                        parent_tran_id
                    )
                )
    except Exception:
        raise


def transaction_exists(tran_id, sched_type):
    """
    check if a transaction of specific type exists
    """
    _sql = """
    SELECT * from public.{}
    WHERE transaction_id = '{}'
    """.format(
        sched_type, tran_id
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute(_sql)
            if cursor.rowcount:
                return True
        return False
    except:
        raise



@lru_cache(maxsize=32)
def populate_transaction_types():
    """
    load all transaction_type data for shced_a and sched_b
    Note: we may need to update this to load all tran_types

    return a dic in the following format:
    {"trans_identifier: (line_number, trans_type)"}

    All transaction types loaded for now, may need to add funtions to load specific transaction types:
    """
    _sql = """
    SELECT tran_identifier as tran_id, line_num as line_num, tran_code as tran_code
    FROM ref_transaction_types 
    """
    # WHERE sched_type = 'sched_a'
    # OR sched_type = 'sched_b'
    # """
    tran_dic = {}
    try:
        with connection.cursor() as cursor:
            cursor.execute(_sql)

            if cursor.rowcount == 0:
                raise Exception("bummer, no transaction_types found in the database.")
            for row in cursor.fetchall():
                tran_dic[row[0]] = (row[1], row[2])
        return tran_dic
    except Exception:
        raise


@lru_cache(maxsize=32)
def get_transaction_type_descriptions():
    """
    load all transaction_type descriptions


    return a dic in the following format:
    {"trans_identifier":"trans_description"}

    All transaction types loaded for now, may need to add funtions to load specific transaction types:
    """
    _sql = """
    SELECT tran_identifier as tran_id, tran_desc
    FROM ref_transaction_types 
    """
    tran_dic = {}
    try:
        with connection.cursor() as cursor:
            cursor.execute(_sql)
            if cursor.rowcount == 0:
                raise Exception("bummer, no transaction_types found in the database.")
            for row in cursor.fetchall():
                tran_dic[row[0]] = row[1]
        # logger.debug("transaction desc loaded:{}".format(tran_dic))
        return tran_dic
    except Exception:
        raise


def get_line_number_trans_type(transaction_type_identifier):
    """
    return corresponding line_num and tran_code(tran_type) for each tran_type_id
    """
    try:
        trans_dic = populate_transaction_types()
        if transaction_type_identifier in trans_dic:
            list_value = trans_dic.get(transaction_type_identifier)
            line_number = list_value[0]
            transaction_type = list_value[1]
            if transaction_type is None:
                transaction_type = 0
            return line_number, transaction_type
        else:
            raise Exception(

                "The transaction type identifier is not in the specified list. Input Received: "
                + transaction_type_identifier
            )

    except:
        raise



def get_sched_a_transactions(
    report_id, cmte_id, transaction_id=None, back_ref_transaction_id=None
):

    """
    load sched_a transacrtions
    """
    try:
        with connection.cursor() as cursor:
            # GET single row from schedA table
            if transaction_id:
                query_string = """
                SELECT cmte_id, report_id, line_number, transaction_type, transaction_id, back_ref_transaction_id, 
                        back_ref_sched_name, entity_id, contribution_date, contribution_amount, aggregate_amt, 
                        purpose_description, memo_code, memo_text, election_code, election_other_description, 
                        create_date, donor_cmte_id, donor_cmte_name, transaction_type_identifier
                FROM public.sched_a 
                WHERE report_id = %s 
                AND cmte_id = %s 
                AND transaction_id = %s 
                AND delete_ind is distinct from 'Y'
                """

                cursor.execute(
                    """SELECT json_agg(t) FROM (""" + query_string + """) t""",
                    [report_id, cmte_id, transaction_id],
                )

            elif back_ref_transaction_id:
                query_string = """
                SELECT cmte_id, report_id, line_number, transaction_type, transaction_id, back_ref_transaction_id, 
                        back_ref_sched_name, entity_id, contribution_date, contribution_amount, aggregate_amt, 
                        purpose_description, memo_code, memo_text, election_code, election_other_description, 
                        create_date, donor_cmte_id, donor_cmte_name, transaction_type_identifier
                FROM public.sched_a 
                WHERE report_id = %s 
                AND cmte_id = %s 
                AND back_ref_transaction_id = %s 
                AND delete_ind is distinct from 'Y'
                """

                cursor.execute(
                    """SELECT json_agg(t) FROM (""" + query_string + """) t""",
                    [report_id, cmte_id, back_ref_transaction_id],
                )

            else:
                query_string = """
                SELECT entity_id, cmte_id, report_id, line_number, transaction_type, transaction_id, back_ref_transaction_id, 
                        back_ref_sched_name, contribution_date, contribution_amount, aggregate_amt, purpose_description, 
                        memo_code, memo_text, election_code, election_other_description, create_date, donor_cmte_id, 
                        donor_cmte_name, transaction_type_identifier
                FROM public.sched_a 
                WHERE report_id = %s 
                AND cmte_id = %s 
                AND delete_ind is distinct from 'Y' 
                ORDER BY transaction_id DESC
                """

                cursor.execute(
                    """SELECT json_agg(t) FROM (""" + query_string + """) t""",
                    [report_id, cmte_id],
                )

            return post_process_it(cursor, cmte_id)
    except Exception:
        raise


def get_sched_e_child_transactions(report_id, cmte_id, transaction_id):
    """
    load child transactions for sched_e
    """
    _sql = """
        SELECT
            cmte_id,
            report_id,
            transaction_type_identifier,
            transaction_id,
            back_ref_transaction_id,
            back_ref_sched_name,
            payee_entity_id,
            election_code,
            election_other_desc,
            expenditure_amount,
            COALESCE(dissemination_date, disbursement_date) as expenditure_date,
            calendar_ytd_amount,
            purpose,
            category_code,
            payee_cmte_id,
            support_oppose_code,
            completing_entity_id,
            date_signed,
            memo_code,
            memo_text,
            line_number,
            create_date, 
            last_update_date
            FROM public.sched_e
            WHERE report_id = %s 
            AND cmte_id = %s 
            AND back_ref_transaction_id = %s 
            AND delete_ind is distinct from 'Y'
            """
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """SELECT json_agg(t) FROM (""" + _sql + """) t""",
                [report_id, cmte_id, transaction_id],
            )
            return post_process_it(cursor, cmte_id)
    except:
        raise


def get_sched_f_child_transactions(report_id, cmte_id, transaction_id):
    """
    load child transactions for sched_f
    """
    _sql = """
    SELECT             
            cmte_id,
            report_id,
            transaction_type_identifier,
            transaction_id, 
            back_ref_transaction_id,
            back_ref_sched_name,
            coordinated_exp_ind,
            designating_cmte_id,
            designating_cmte_name,
            subordinate_cmte_id,
            subordinate_cmte_name,
            subordinate_cmte_street_1,
            subordinate_cmte_street_2,
            subordinate_cmte_city,
            subordinate_cmte_state,
            subordinate_cmte_zip,
            payee_entity_id,
            expenditure_date,
            expenditure_amount,
            aggregate_general_elec_exp,
            purpose,
            category_code,
            payee_cmte_id,
            payee_cand_id,
            payee_cand_last_name,
            payee_cand_fist_name,
            payee_cand_middle_name,
            payee_cand_prefix,
            payee_cand_suffix,
            payee_cand_office,
            payee_cand_state,
            payee_cand_district,
            memo_code,
            memo_text,
            create_date
    FROM public.sched_f 
    WHERE report_id = %s 
    AND cmte_id = %s 
    AND back_ref_transaction_id = %s 
    AND delete_ind is distinct from 'Y'
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """SELECT json_agg(t) FROM (""" + _sql + """) t""",
                [report_id, cmte_id, transaction_id],
            )
            return post_process_it(cursor, cmte_id)
    except:
        raise


def get_sched_h4_child_transactions(report_id, cmte_id, transaction_id):
    """
    load child transactions for sched_h4
    TODO: those chiuld trnasaction functions can be refatored later on
    """
    _sql = """
    SELECT             
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
            create_date
    FROM public.sched_h4 
    WHERE report_id = %s 
    AND cmte_id = %s 
    AND back_ref_transaction_id = %s 
    AND delete_ind is distinct from 'Y'
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """SELECT json_agg(t) FROM (""" + _sql + """) t""",
                [report_id, cmte_id, transaction_id],
            )
            return post_process_it_h4(cursor, cmte_id)
    except:
        raise


def get_sched_h6_child_transactions(report_id, cmte_id, transaction_id):
    """
    load child transactions for sched_h6
    """
    _sql = """
    SELECT             
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
            (
                CASE
                WHEN activity_event_type = 'VR' THEN 'Voter Registration'
                WHEN activity_event_type = 'GO' THEN 'GOTV'
                WHEN activity_event_type = 'VI' THEN 'Voter ID'
                WHEN activity_event_type = 'GC' THEN 'Generic Campaign' 
                ELSE ''::text
                END) AS activity_event_identifier, 
            memo_code,
            memo_text, 
            create_date
    FROM public.sched_h6
    WHERE report_id = %s 
    AND cmte_id = %s 
    AND back_ref_transaction_id = %s 
    AND delete_ind is distinct from 'Y'
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """SELECT json_agg(t) FROM (""" + _sql + """) t""",
                [report_id, cmte_id, transaction_id],
            )
            return post_process_it(cursor, cmte_id)
    except:
        raise


def get_sched_c_loan_payments(cmte_id, transaction_id):
    """
    load loan payments for a particular loan based on transaction_id
    """
    _sql = """
    SELECT             
            cmte_id,
            report_id,
            transaction_id,
            back_ref_transaction_id,
            expenditure_date,
            expenditure_amount,
            transaction_type_identifier, 
            expenditure_purpose, 
            memo_text
    FROM public.sched_b
    WHERE cmte_id = %s 
    AND back_ref_transaction_id = %s 
    AND delete_ind is distinct from 'Y'
    """
    try:
        # if report_id:
        # _sql = _sql + 'AND report_id = {}'.format(report_id)
        with connection.cursor() as cursor:
            cursor.execute(
                """SELECT json_agg(t) FROM (""" + _sql + """) t""",
                [cmte_id, transaction_id],
            )
            return post_process_it(cursor, cmte_id)
    except:
        raise


def get_sched_c1_child(cmte_id, transaction_id):
    """
    load child transactions for sched_f without report_id
    """
    # print(report_id)
    # print(transaction_id)
    _sql = """
    SELECT             
            cmte_id,
            report_id,
            line_number,
            transaction_type_identifier,
            transaction_type,
            transaction_id,
            back_ref_transaction_id,
            back_ref_sched_name,
            lender_entity_id,
            loan_amount,
            loan_intrest_rate,
            loan_incurred_date,
            loan_due_date,
            is_loan_restructured,
            original_loan_date,
            credit_amount_this_draw,
            total_outstanding_balance,
            other_parties_liable,
            pledged_collateral_ind,
            pledge_collateral_desc,
            pledge_collateral_amount,
            perfected_intrest_ind,
            future_income_ind,
            future_income_desc,
            future_income_estimate,
            depository_account_established_date,
            depository_account_location,
            depository_account_street_1,
            depository_account_street_2,
            depository_account_city,
            depository_account_state,
            depository_account_zip,
            depository_account_auth_date,
            basis_of_loan_desc,
            treasurer_entity_id,
            treasurer_signed_date,
            authorized_entity_id,
            authorized_entity_title,
            authorized_signed_date,
            create_date
    FROM public.sched_c1
    WHERE cmte_id = %s 
    AND back_ref_transaction_id = %s 
    AND delete_ind is distinct from 'Y'
    """
    try:
        # if report_id:
        # _sql = _sql + 'AND report_id = {}'.format(report_id)
        with connection.cursor() as cursor:
            cursor.execute(
                """SELECT json_agg(t) FROM (""" + _sql + """) t""",
                [cmte_id, transaction_id],
            )
            return post_process_it(cursor, cmte_id)
    except:
        raise


def get_sched_c1_child_transactions(cmte_id, transaction_id):
    """
    load child transactions for sched_f without report_id
    """
    # print(report_id)
    # print(transaction_id)
    _sql = """
        SELECT             
            cmte_id,
            transaction_id
        FROM public.sched_c1
        WHERE cmte_id = %s 
        AND back_ref_transaction_id = %s 
        AND delete_ind is distinct from 'Y'
    """
    # _sql = """
    # SELECT
    #         cmte_id,
    #         report_id,
    #         line_number,
    #         transaction_type_identifier,
    #         transaction_type,
    #         transaction_id,
    #         back_ref_transaction_id,
    #         back_ref_sched_name,
    #         lender_entity_id,
    #         loan_amount,
    #         loan_intrest_rate,
    #         loan_incurred_date,
    #         loan_due_date,
    #         is_loan_restructured,
    #         original_loan_date,
    #         credit_amount_this_draw,
    #         total_outstanding_balance,
    #         other_parties_liable,
    #         pledged_collateral_ind,
    #         pledge_collateral_desc,
    #         pledge_collateral_amount,
    #         perfected_intrest_ind,
    #         future_income_ind,
    #         future_income_desc,
    #         future_income_estimate,
    #         depository_account_established_date,
    #         depository_account_location,
    #         depository_account_street_1,
    #         depository_account_street_2,
    #         depository_account_city,
    #         depository_account_state,
    #         depository_account_zip,
    #         depository_account_auth_date,
    #         basis_of_loan_desc,
    #         treasurer_entity_id,
    #         treasurer_signed_date,
    #         authorized_entity_id,
    #         authorized_entity_title,
    #         authorized_signed_date,
    #         create_date
    # FROM public.sched_c1
    # WHERE cmte_id = %s
    # AND back_ref_transaction_id = %s
    # AND delete_ind is distinct from 'Y'
    # """
    try:
        # if report_id:
        # _sql = _sql + 'AND report_id = {}'.format(report_id)
        with connection.cursor() as cursor:
            cursor.execute(
                """SELECT json_agg(t) FROM (""" + _sql + """) t""",
                [cmte_id, transaction_id],
            )
            return cursor.fetchone()[0]
            # return post_process_it(cursor, cmte_id)
    except:
        rais


def get_sched_c2_child_transactions(cmte_id, transaction_id):
    """
    load child transactions for sched_f
    """
    # _sql = """
    # SELECT
    #         cmte_id,
    #         report_id,
    #         line_number,
    #         transaction_type_identifier,
    #         guarantor_entity_id,
    #         guaranteed_amount,
    #         transaction_id,
    #         back_ref_transaction_id,
    #         back_ref_sched_name,
    #         create_date
    # FROM public.sched_c2
    # WHERE cmte_id = %s
    # AND back_ref_transaction_id = %s
    # AND delete_ind is distinct from 'Y'
    # """
    _sql = """
    SELECT             
            cmte_id,
            transaction_id
    FROM public.sched_c2
    WHERE cmte_id = %s 
    AND back_ref_transaction_id = %s 
    AND delete_ind is distinct from 'Y'
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """SELECT json_agg(t) FROM (""" + _sql + """) t""",
                [cmte_id, transaction_id],
            )
            return post_process_it(cursor, cmte_id)
    except:
        raise


def get_sched_c2_child(cmte_id, transaction_id):
    """
    load c2 child transactions for sched_c without report_id
    """
    _sql = """
    SELECT             
            cmte_id,
            report_id,
            line_number,
            transaction_type_identifier,
            guarantor_entity_id,
            guaranteed_amount,
            transaction_id,
            back_ref_transaction_id,
            back_ref_sched_name,
            create_date
    FROM public.sched_c2
    WHERE cmte_id = %s 
    AND back_ref_transaction_id = %s 
    AND delete_ind is distinct from 'Y'
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """SELECT json_agg(t) FROM (""" + _sql + """) t""",
                [cmte_id, transaction_id],
            )
            return post_process_it(cursor, cmte_id)
    except:
        raise


def get_sched_b_transactions(
    report_id, cmte_id, include_deleted_trans_flag = False, transaction_id=None, back_ref_transaction_id=None
):

    """
    load sched_b transactions
    """
    try:
        report_list = superceded_report_id_list(report_id)
        with connection.cursor() as cursor:
            # GET child rows from schedB table
            if transaction_id:
                if not include_deleted_trans_flag:
                    query_string = """
                    SELECT cmte_id, report_id, line_number, transaction_type, 
                                            transaction_id, back_ref_transaction_id, back_ref_sched_name, 
                                            entity_id, expenditure_date, expenditure_amount, 
                                            semi_annual_refund_bundled_amount, expenditure_purpose, 
                                            category_code, memo_code, memo_text, election_code, 
                                            election_other_description, beneficiary_cmte_id, 
                                            other_name, other_street_1, 
                                            other_street_2, other_city, other_state, other_zip, 
                                            nc_soft_account, transaction_type_identifier, 
                                            beneficiary_cmte_name,
                                            beneficiary_cand_entity_id,
                                            levin_account_id,
                                            aggregate_amt,
                                            create_date,
                                            redesignation_id, redesignation_ind
                    FROM public.sched_b WHERE report_id in ('{}')
                    AND cmte_id = %s 
                    AND transaction_id = %s 
                    AND delete_ind is distinct from 'Y'
                    """.format(
                        "', '".join(report_list)
                    )
                else:
                    query_string = """
                    SELECT cmte_id, report_id, line_number, transaction_type, 
                                            transaction_id, back_ref_transaction_id, back_ref_sched_name, 
                                            entity_id, expenditure_date, expenditure_amount, 
                                            semi_annual_refund_bundled_amount, expenditure_purpose, 
                                            category_code, memo_code, memo_text, election_code, 
                                            election_other_description, beneficiary_cmte_id, 
                                            other_name, other_street_1, 
                                            other_street_2, other_city, other_state, other_zip, 
                                            nc_soft_account, transaction_type_identifier, 
                                            beneficiary_cmte_name,
                                            beneficiary_cand_entity_id,
                                            levin_account_id,
                                            aggregate_amt,
                                            create_date,
                                            aggregation_ind,
                                            redesignation_id, redesignation_ind
                    FROM public.sched_b WHERE report_id in ('{}')
                    AND cmte_id = %s 
                    AND transaction_id = %s 
                    """.format(
                        "', '".join(report_list)
                    )

                cursor.execute(
                    """SELECT json_agg(t) FROM (""" + query_string + """) t""",
                    [cmte_id, transaction_id],
                )
            elif back_ref_transaction_id:
                query_string = """
                SELECT  cmte_id, report_id, line_number, transaction_type, transaction_id, back_ref_transaction_id, 
                        back_ref_sched_name, entity_id, expenditure_date, expenditure_amount, semi_annual_refund_bundled_amount, 
                        expenditure_purpose, category_code, memo_code, memo_text, election_code, election_other_description, 
                        beneficiary_cmte_id, other_name, other_street_1, other_street_2, other_city, 
                        other_state, other_zip, nc_soft_account, transaction_type_identifier, 
                        beneficiary_cmte_name,
                        beneficiary_cand_entity_id,
                        levin_account_id,
                        aggregate_amt,
                        create_date
                FROM public.sched_b 
                WHERE report_id in ('{}')
                AND cmte_id = %s 
                AND back_ref_transaction_id = %s 
                AND delete_ind is distinct from 'Y'
                """.format(
                    "', '".join(report_list)
                )
                cursor.execute(
                    """SELECT json_agg(t) FROM (""" + query_string + """) t""",
                    [cmte_id, back_ref_transaction_id],
                )
            else:
                query_string = """
                SELECT  cmte_id, report_id, line_number, transaction_type, transaction_id, back_ref_transaction_id, 
                        back_ref_sched_name, entity_id, expenditure_date, expenditure_amount, semi_annual_refund_bundled_amount, 
                        expenditure_purpose, category_code, memo_code, memo_text, election_code, election_other_description, 
                        beneficiary_cmte_id, other_name, other_street_1, other_street_2, other_city, 
                        other_state, other_zip, nc_soft_account, transaction_type_identifier, 
                        beneficiary_cmte_name,
                        beneficiary_cand_entity_id,
                        levin_account_id,
                        aggregate_amt,
                        create_date
                FROM public.sched_b 
                WHERE report_id in ('{}')
                AND cmte_id = %s 
                AND delete_ind is distinct from 'Y'
                """.format(
                    "', '".join(report_list)
                )
                cursor.execute(
                    """SELECT json_agg(t) FROM (""" + query_string + """) t""",
                    [cmte_id],
                )
            return post_process_it(cursor, cmte_id)
    except Exception:
        raise


def candify_it(cand_json):
    """
    a helper function to add 'cand_' to cand_entity fields
    """
    candify_item = {}
    for _f in cand_json:
        if _f == "entity_id":
            candify_item["beneficiary_cand_entity_id"] = cand_json.get("entity_id")
        elif _f == "ref_cand_cmte_id":
            candify_item["beneficiary_cand_id"] = cand_json.get("ref_cand_cmte_id")
            candify_item["cand_id"] = cand_json.get("ref_cand_cmte_id")
        elif _f in ["occupation", "employer"]:
            continue
        elif not _f.startswith("cand"):
            candify_item["cand_" + _f] = cand_json.get(_f)
        else:
            candify_item[_f] = cand_json.get(_f)
    return candify_item


def post_process_it_h4(cursor, cmte_id):
    """
    helper function:
    merge transactions and entities after transactions are loaded
    """
    transaction_list = cursor.fetchone()[0]
    if not transaction_list:
        return []
    # if not transaction_list:
    #     if (
    #         not back_ref_transaction_id
    #     ):  # raise exception for non_child transaction loading
    #         raise NoOPError(
    #             "No transactions found."
    #         )
    #     else:  # return empy list for child transaction loading
    #         return []
    merged_list = []
    for item in transaction_list:
        entity_id = item.get("payee_entity_id")
        data = {"entity_id": entity_id, "cmte_id": cmte_id}
        entity_list = get_entities(data)
        dictEntity = entity_list[0]
        # cand_entity = {}
        # if item.get("beneficiary_cand_entity_id"):
        #     cand_data = {
        #         "entity_id": item.get("beneficiary_cand_entity_id"),
        #         "cmte_id": cmte_id,
        #     }
        #     cand_entity = get_entities(cand_data)[0]
        #     cand_entity = candify_it(cand_entity)

        merged_dict = {**item, **dictEntity}
        merged_list.append(merged_dict)
    return merged_list


def post_process_it(cursor, cmte_id):
    """
    helper function:
    merge transactions and entities after transactions are loaded
    """
    transaction_list = cursor.fetchone()[0]
    if not transaction_list:
        return []
    # if not transaction_list:
    #     if (
    #         not back_ref_transaction_id
    #     ):  # raise exception for non_child transaction loading
    #         raise NoOPError(
    #             "No transactions found."
    #         )
    #     else:  # return empy list for child transaction loading
    #         return []
    merged_list = []
    for item in transaction_list:

        entity_id = item.get("entity_id")
        data = {"entity_id": entity_id, "cmte_id": cmte_id}

        entity_list = get_entities(data)
        dictEntity = entity_list[0]
        cand_entity = {}
        if item.get("beneficiary_cand_entity_id"):
            cand_data = {
                "entity_id": item.get("beneficiary_cand_entity_id"),
                "cmte_id": cmte_id,
            }
            cand_entity = get_entities(cand_data)[0]
            cand_entity = candify_it(cand_entity)

        merged_dict = {**item, **dictEntity, **cand_entity}
        merged_list.append(merged_dict)
    return merged_list
