import logging
from functools import wraps

# from functools import lru_cache
from django.db import connection

# from fecfiler.core.views import get_entities, NoOPError, superceded_report_id_list
import datetime

# for updating ear receipt memo
EAR_RECEIPT_MEMO = [
    "EAR_REC",
    "PAC_EAR_REC",
    "EAR_REC_RECNT_ACC",
    "EAR_REC_CONVEN_ACC",
    "EAR_REC_HQ_ACC",
]

# for updating ear out memo
EAR_OUT_MEMO = ["CON_EAR_DEP", "CON_EAR_UNDEP", "PAC_CON_EAR_DEP", "PAC_CON_EAR_UNDEP"]

logger = logging.getLogger(__name__)


def update_earmark_memo_contribution(transaction_id, contribution_amount):
    """
    helper function for updating memo earmark transaction amount when parent changes
    """
    _sql1 = """
    SELECT aggregate_amt FROM public.sched_a
    WHERE transaction_id = %s
    AND delete_ind is distinct from 'Y'
    """
    _sql2 = """
    UPDATE public.sched_a
    SET contribution_amount = %s,
        aggregate_amt = %s
    WHERE back_ref_transaction_id = %s
    AND delete_ind is distinct from 'Y'
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(_sql1, [transaction_id])
            aggregate_amt = cursor.fetchone()[0]
            logger.debug(
                "update earmark memo with contribution {} and aggregate {}".format(
                    contribution_amount, aggregate_amt
                )
            )
            cursor.execute(_sql2, [contribution_amount, aggregate_amt, transaction_id])
            if cursor.rowcount == 0:
                logger.debug("no memo transaction found.")
                # raise Exception("Error: updating earmark memo failed.")
    except BaseException:
        raise


def new_memo_contribution_amount(func):
    """
    a decorator for updating earmark memo tranasctions when parent transaction is updated.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        res = func(*args, **kwargs)
        # logger.debug("update report last_update_date after {}".format(func.__name__))
        if res.get("transaction_type_identifier") in EAR_RECEIPT_MEMO:
            logger.debug(
                "update memo earmark contribution amount after {}".format(func.__name__)
            )
            transaction_id = res.get("transaction_id")
            contribution_amount = res.get("contribution_amount")
            # aggregate_amt = res.get("aggregate_amt")
            update_earmark_memo_contribution(transaction_id, contribution_amount)
            logger.debug("memo transaction amount updated.")
        return res

    return wrapper


def update_earmark_out_expenditure(transaction_id, contribution_amount):
    """
    helper function for updating earmark out expenditure amount when parent earmark
    transaction is updated
    """
    _sql = """
    UPDATE public.sched_b
    SET expenditure_amount = %s
    WHERE back_ref_transaction_id = %s
    AND delete_ind is distinct from 'Y'
    """
    try:
        with connection.cursor() as cursor:
            # cursor.execute(_sql1, [transaction_id])
            # aggregate_amt = cursor.fetchone()[0]
            logger.debug(
                "update earmark out memo with contribution amount {}".format(
                    contribution_amount
                )
            )
            cursor.execute(_sql, [contribution_amount, transaction_id])
            # if cursor.rowcount == 0:
            #     raise Exception("Error: updating earmark out memo failed.")
    except BaseException:
        raise


def new_earmarkout_expenditure_amount(func):
    """
    a decorator for updating earmark out tranasctions when parent transaction is updated.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        res = func(*args, **kwargs)
        # logger.debug("update report last_update_date after {}".format(func.__name__))
        if res.get("transaction_type_identifier") in EAR_OUT_MEMO:
            logger.debug(
                "update memo earmark contribution amount after {}".format(func.__name__)
            )
            transaction_id = res.get("transaction_id")
            contribution_amount = res.get("contribution_amount")
            # aggregate_amt = res.get("aggregate_amt")
            update_earmark_out_expenditure(transaction_id, contribution_amount)
            logger.debug("ear-out memo transaction amount updated.")
        return res

    return wrapper
