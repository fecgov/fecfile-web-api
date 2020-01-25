import logging
import datetime

# from functools import lru_cache
from django.db import connection

# from fecfiler.core.views import get_entities, NoOPError, superceded_report_id_list
# import datetime

logger = logging.getLogger(__name__)


def date_format(cvg_date):
    try:
        if cvg_date == None or cvg_date in ["none", "null", " ", ""]:
            return None
        cvg_dt = datetime.datetime.strptime(cvg_date, "%Y-%m-%d").date()
        return cvg_dt
    except:
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
        expenditure_dt = date_format(data.get("expenditure_date"))
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

