from functools import lru_cache
from django.db import connection


@lru_cache(maxsize=32)
def populate_transaction_types():
    """
    load all transaction_type data for shced_a and sched_b
    Note: we may need to update this to load all tran_types

    return a dic in the following format:
    {"trans_identifier: (line_number, trans_type)"}
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
