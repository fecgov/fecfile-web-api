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
            last_update_date
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
            merged_list = []
            for dictF in schedF_list:
                entity_id = dictF.get("entity_id")
                data = {"entity_id": entity_id, "cmte_id": cmte_id}
                entity_list = get_entities(data)
                dictEntity = entity_list[0]
                del dictEntity["cand_office"]
                del dictEntity["cand_office_state"]
                del dictEntity["cand_office_district"]
                merged_dict = {**dictF, **dictEntity}
                merged_list.append(merged_dict)
        return merged_list
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

