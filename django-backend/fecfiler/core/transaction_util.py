from functools import lru_cache
from django.db import connection
from fecfiler.core.views import get_entities


@lru_cache(maxsize=32)
def populate_transaction_types():
    """
    load all transaction_type data for shced_a and sched_b
    Note: we may need to update this to load all tran_types

    return a dic in the following format:
    {"trans_identifier: (line_number, trans_type)"}
    # TODO: may need to update this function to include other transaction types
    """
    _sql = """
    SELECT tran_identifier as tran_id, line_num as line_num, tran_code as tran_code
    FROM ref_transaction_types 
    WHERE sched_type = 'sched_a'
    OR sched_type = 'sched_b'
    """
    tran_dic = {}
    try:
        with connection.cursor() as cursor:
            cursor.execute(_sql)
            if (cursor.rowcount == 0):
                raise Exception(
                    'no transaction_types found for sched_a')
            for row in cursor.fetchall():
                tran_dic[row[0]] = (row[1], row[2])
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
            return line_number, transaction_type
        else:
            raise Exception(
                'The transaction type identifier is not in the specified list')
    except:
        raise


def get_sched_a_transactions(report_id, cmte_id, transaction_id=None, back_ref_transaction_id=None):
    """
    load sched_a transacrtions
    """
    try:
        with connection.cursor() as cursor:
            # GET single row from schedA table
            if transaction_id:
                query_string = """SELECT cmte_id, report_id, line_number, transaction_type, transaction_id, back_ref_transaction_id, back_ref_sched_name, entity_id, contribution_date, contribution_amount, aggregate_amt, purpose_description, memo_code, memo_text, election_code, election_other_description, create_date, donor_cmte_id, donor_cmte_name, transaction_type_identifier
                                FROM public.sched_a WHERE report_id = %s AND cmte_id = %s AND transaction_id = %s AND delete_ind is distinct from 'Y'"""

                cursor.execute("""SELECT json_agg(t) FROM (""" + query_string +
                               """) t""", [report_id, cmte_id, transaction_id])
            elif back_ref_transaction_id:
                query_string = """SELECT cmte_id, report_id, line_number, transaction_type, transaction_id, back_ref_transaction_id, back_ref_sched_name, entity_id, contribution_date, contribution_amount, aggregate_amt, purpose_description, memo_code, memo_text, election_code, election_other_description, create_date, donor_cmte_id, donor_cmte_name, transaction_type_identifier
                            FROM public.sched_a WHERE report_id = %s AND cmte_id = %s AND back_ref_transaction_id = %s AND delete_ind is distinct from 'Y'"""

                cursor.execute("""SELECT json_agg(t) FROM (""" + query_string +
                               """) t""", [report_id, cmte_id, back_ref_transaction_id])
            else:
                query_string = """SELECT entity_id, cmte_id, report_id, line_number, transaction_type, transaction_id, back_ref_transaction_id, back_ref_sched_name, contribution_date, contribution_amount, aggregate_amt, purpose_description, memo_code, memo_text, election_code, election_other_description, create_date, donor_cmte_id, donor_cmte_name, transaction_type_identifier
                            FROM public.sched_a WHERE report_id = %s AND cmte_id = %s AND delete_ind is distinct from 'Y' ORDER BY transaction_id DESC"""

                cursor.execute("""SELECT json_agg(t) FROM (""" +
                               query_string + """) t""", [report_id, cmte_id])
        return post_process_it(cursor, cmte_id)
        #     schedA_list = cursor.fetchone()[0]
        #     if not schedA_list:
        #         raise NoOPError(
        #             'No transaction found for cmte_id {} and report_id {}'.format(cmte_id, report_id))
        #     merged_list = []
        #     for dictA in schedA_list:
        #         entity_id = dictA.get('entity_id')
        #         data = {
        #             'entity_id': entity_id,
        #             'cmte_id': cmte_id
        #         }
        #         entity_list = get_entities(data)
        #         dictEntity = entity_list[0]
        #         merged_dict = {**dictA, **dictEntity}
        #         merged_list.append(merged_dict)
        # return merged_list
    except Exception:
        raise


def get_sched_b_transactions(report_id, cmte_id, transaction_id=None, back_ref_transaction_id=None):
    """
    load sched_b transactions
    """
    try:
        with connection.cursor() as cursor:
            # GET child rows from schedB table
            if transaction_id:
                query_string = """SELECT cmte_id, report_id, line_number, transaction_type, transaction_id, back_ref_transaction_id, back_ref_sched_name, entity_id, expenditure_date, expenditure_amount, semi_annual_refund_bundled_amount, expenditure_purpose, category_code, memo_code, memo_text, election_code, election_other_description, beneficiary_cmte_id, beneficiary_cand_id, other_name, other_street_1, other_street_2, other_city, other_state, other_zip, nc_soft_account, transaction_type_identifier, create_date
                            FROM public.sched_b WHERE report_id = %s AND cmte_id = %s AND transaction_id = %s AND delete_ind is distinct from 'Y'"""
                cursor.execute(
                    """SELECT json_agg(t) FROM (""" + query_string + """) t""",
                    [report_id, cmte_id, transaction_id],
                )
            elif back_ref_transaction_id:
                query_string = """SELECT cmte_id, report_id, line_number, transaction_type, transaction_id, back_ref_transaction_id, back_ref_sched_name, entity_id, expenditure_date, expenditure_amount, semi_annual_refund_bundled_amount, expenditure_purpose, category_code, memo_code, memo_text, election_code, election_other_description, beneficiary_cmte_id, beneficiary_cand_id, other_name, other_street_1, other_street_2, other_city, other_state, other_zip, nc_soft_account, transaction_type_identifier, create_date
                            FROM public.sched_b WHERE report_id = %s AND cmte_id = %s AND back_ref_transaction_id = %s AND delete_ind is distinct from 'Y'"""
                cursor.execute(
                    """SELECT json_agg(t) FROM (""" + query_string + """) t""",
                    [report_id, cmte_id, back_ref_transaction_id],
                )
            else:
                query_string = """SELECT cmte_id, report_id, line_number, transaction_type, transaction_id, back_ref_transaction_id, back_ref_sched_name, entity_id, expenditure_date, expenditure_amount, semi_annual_refund_bundled_amount, expenditure_purpose, category_code, memo_code, memo_text, election_code, election_other_description, beneficiary_cmte_id, beneficiary_cand_id, other_name, other_street_1, other_street_2, other_city, other_state, other_zip, nc_soft_account, transaction_type_identifier, create_date
                            FROM public.sched_b WHERE report_id = %s AND cmte_id = %s AND delete_ind is distinct from 'Y'"""
                cursor.execute(
                    """SELECT json_agg(t) FROM (""" + query_string + """) t""",
                    [report_id, cmte_id],
                )
        return post_process_it(cursor, cmte_id)
        #     for row in cursor.fetchall():
        #         data_row = list(row)
        #         schedB_list = data_row[0]
        #     merged_list = []
        #     if not (schedB_list is None):
        #         for dictB in schedB_list:
        #             entity_id = dictB.get("entity_id")
        #             data = {"entity_id": entity_id, "cmte_id": cmte_id}
        #             entity_list = get_entities(data)
        #             dictEntity = entity_list[0]
        #             merged_dict = {**dictB, **dictEntity}
        #             merged_list.append(merged_dict)
        # return merged_list
    except Exception:
        raise


def post_process_it(cursor, cmte_id):
    """
    helper function:
    merge transactions and entities after transactions are loaded
    """
    transaction_list = cursor.fetchone()[0]
    if not transaction_list:
        raise NoOPError(
            'No transactions found for current report.')  # cmte_id {} and report_id {}'.format(cmte_id, report_id))
    merged_list = []
    for item in transaction_list:
        entity_id = item.get('entity_id')
        data = {
            'entity_id': entity_id,
            'cmte_id': cmte_id
        }
        entity_list = get_entities(data)
        dictEntity = entity_list[0]
        merged_dict = {**item, **dictEntity}
        merged_list.append(merged_dict)
    return merged_list
