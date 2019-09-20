from functools import lru_cache
from django.db import connection
from fecfiler.core.views import get_entities, NoOPError


def update_parent_purpose(data):
    """
    for earmark transaction only:
    when a earmark child transactions is added or updated,
    the child entity_name should be update in parents 
    'purpose_description' field
    """
    parent_tran_id = data.get("back_ref_transaction_id")
    cmte_id = data.get("cmte_id")
    report_id = data.get("report_id")
    entity_name = data.get("entity_name")
    purpose = "Earmark for " + entity_name
    _sql = """
    UPDATE public.sched_a 
    SET purpose_description = %s 
    WHERE transaction_id = %s AND report_id = %s AND cmte_id = %s 
    AND delete_ind is distinct from 'Y'
    """
    try:
        with connection.cursor() as cursor:
            # Insert data into schedA table
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
            return post_process_it(cursor, cmte_id, report_id, back_ref_transaction_id)
    except Exception:
        raise


def get_sched_b_transactions(
    report_id, cmte_id, transaction_id=None, back_ref_transaction_id=None
):
    """
    load sched_b transactions
    """
    try:
        with connection.cursor() as cursor:
            # GET child rows from schedB table
            if transaction_id:
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
                                        aggregate_amt,
                                        create_date
                FROM public.sched_b WHERE report_id = %s 
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
                SELECT  cmte_id, report_id, line_number, transaction_type, transaction_id, back_ref_transaction_id, 
                        back_ref_sched_name, entity_id, expenditure_date, expenditure_amount, semi_annual_refund_bundled_amount, 
                        expenditure_purpose, category_code, memo_code, memo_text, election_code, election_other_description, 
                        beneficiary_cmte_id, other_name, other_street_1, other_street_2, other_city, 
                        other_state, other_zip, nc_soft_account, transaction_type_identifier, 
                        beneficiary_cmte_name,
                        aggregate_amt,
                        create_date
                FROM public.sched_b 
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
                SELECT  cmte_id, report_id, line_number, transaction_type, transaction_id, back_ref_transaction_id, 
                        back_ref_sched_name, entity_id, expenditure_date, expenditure_amount, semi_annual_refund_bundled_amount, 
                        expenditure_purpose, category_code, memo_code, memo_text, election_code, election_other_description, 
                        beneficiary_cmte_id, other_name, other_street_1, other_street_2, other_city, 
                        other_state, other_zip, nc_soft_account, transaction_type_identifier, 
                        beneficiary_cmte_name,
                        aggregate_amt,
                        create_date
                FROM public.sched_b 
                WHERE report_id = %s 
                AND cmte_id = %s 
                AND delete_ind is distinct from 'Y'
                """
                cursor.execute(
                    """SELECT json_agg(t) FROM (""" + query_string + """) t""",
                    [report_id, cmte_id],
                )
            return post_process_it(cursor, cmte_id, report_id, back_ref_transaction_id)
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
        elif not _f.startswith("cand"):
            candify_item["cand_" + _f] = cand_json.get(_f)
        else:
            candify_item[_f] = cand_json.get(_f)
    return candify_item


def post_process_it(cursor, cmte_id, report_id, back_ref_transaction_id):
    """
    helper function:
    merge transactions and entities after transactions are loaded
    """
    transaction_list = cursor.fetchone()[0]
    if not transaction_list:
        if (
            not back_ref_transaction_id
        ):  # raise exception for non_child transaction loading
            raise NoOPError(
                "No transactions found for current report {}".format(report_id)
            )
        else:  # return empy list for child transaction loading
            return []
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
