import logging
# from functools import lru_cache
from django.db import connection
# from fecfiler.core.views import get_entities, NoOPError, superceded_report_id_list
# import datetime

logger = logging.getLogger(__name__)


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
                return cursor.fetchone()[0] == 'PAC'
        return False
    except:
        raise


def is_pty(cmte_id):
    _sql = """
    SELECT cmte_type_category
    FROM public.committee_master
    WHERE cmte_id = %s;
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(_sql, [cmte_id])
            if cursor.rowcount > 0:
                return cursor.fetchone()[0] == 'PTY'
        return False
    except:
        raise


def do_pty_h1_carryover(cmte_id, report_id):
    """
    check if there is h1 item exist or not:
    if yes:
        no carryover
    else:
        do carryover - grab the most recent h1 item 
        and clone it with current report id
    """

    count_sql = """
    select transaction_id from public.sched_h1
    where cmte_id = %s and report_id = %s
    and delete_ind is distinct from 'Y';
    """

    carryover_sql = """
    INSERT INTO sched_h1 
            (cmte_id, 
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
             back_ref_transaction_id, 
             create_date) 
    SELECT h1.cmte_id, 
        %s, 
        h1.line_number, 
        h1.transaction_type_identifier, 
        h1.transaction_type, 
        get_next_transaction_id('SH'), 
        h1.presidential_only, 
        h1.presidential_and_senate, 
        h1.senate_only, 
        h1.non_pres_and_non_senate, 
        h1.federal_percent, 
        h1.non_federal_percent, 
        h1.election_year, 
        h1.administrative, 
        h1.generic_voter_drive, 
        h1.public_communications, 
        h1.transaction_id, 
        Now() 
    FROM   (SELECT cmte_id, 
                Max(create_date) AS create_date 
            FROM   sched_h1 
            GROUP  BY cmte_id) AS max_h1 
        JOIN sched_h1 h1 
            ON max_h1.cmte_id = h1.cmte_id 
                AND max_h1.create_date = h1.create_date 
                AND h1.cmte_id = %s 
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(count_sql, (cmte_id, report_id))
            print(cursor.fetchone())
            print(cursor.rowcount)
            if not cursor.rowcount:
                logger.debug('no h1 found in current report. need carryover:')
                cursor.execute(carryover_sql, (report_id, cmte_id))
                if cursor.rowcount != 1:
                    logger.debug('no valid h1 found for carryover.')
            logger.debug('pty h1 carryover done.')
    except:
        raise


def do_pac_h1_carryover(cmte_id, report_id):
    """
    check if there is outstanding h1 item exist or not:
    if yes:
        do carryover
    else:
        no carryover

    outstanding h1: non-parent h1(back_ref_transaction_id is null)
    also, need to check report date and only do forward carryover
    """
    # count_sql = """
    # select count(*) from public sched_h1
    # where cmte_id = %s and report_id = %s
    # and delete_ind is distinct from 'Y'
    # """
    carryover_sql = """
    INSERT INTO sched_h1 
            (cmte_id, 
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
             back_ref_transaction_id, 
             create_date) 
    SELECT h.cmte_id, 
        %s, 
        h.line_number, 
        h.transaction_type_identifier, 
        h.transaction_type, 
        get_next_transaction_id('SH'), 
        h.presidential_only, 
        h.presidential_and_senate, 
        h.senate_only, 
        h.non_pres_and_non_senate, 
        h.federal_percent, 
        h.non_federal_percent, 
        h.election_year, 
        h.administrative, 
        h.generic_voter_drive, 
        h.public_communications, 
        h.transaction_id, 
        Now() 
    FROM  public.sched_h1 h, public.reports r
            WHERE 
            h.cmte_id = %s
            AND h.report_id = r.report_id
            AND r.cvg_start_date < (
                        SELECT r.cvg_start_date
                        FROM   public.reports r
                        WHERE  r.report_id = %s
                    )
            AND h.transaction_id NOT In (
                select distinct t.back_ref_transaction_id from public.sched_h1 t
                where t.cmte_id = %s
                and t.back_ref_transaction_id is not null
            )
            AND h.delete_ind is distinct from 'Y'
    """
    try:
        with connection.cursor() as cursor:
            # cursor.execute(count_sql, (report_id, cmte_id, report_id, cmte_id))
            # if cursor.rowcount == 0:
            cursor.execute(carryover_sql, (report_id,
                                           cmte_id, report_id, cmte_id))
            logger.debug(
                'pac h1 carryover done, carryover items:{}'.format(cursor.rowcount))

            # if cursor.rowcount != 1:
            #         raise Exception('error on h1 carryover.')
    except:
        raise


def do_h1_carryover(cmte_id, report_id):
    """
    doing h1 carryover
    """
    logger.debug('doing h1 caryover with cmte_id {} and report_id {}'.format(
        cmte_id, report_id))
    if is_pty(cmte_id):
        logger.debug('party h1 carryover...')
        do_pty_h1_carryover(cmte_id, report_id)
    elif is_pac(cmte_id):
        logger.debug('pac h1 carryover...')
        do_pac_h1_carryover(cmte_id, report_id)
    else:
        pass


def do_h2_carryover(cmte_id, report_id):
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
                    create_date
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
        logger.debug('doing h2 carryover...')
        with connection.cursor() as cursor:
            cursor.execute(_sql, (report_id, cmte_id, report_id, report_id, cmte_id))
            if cursor.rowcount == 0:
                logger.debug('No valid h2 items found.')
            logger.debug(
                'h2 carryover done with report_id {}'.format(report_id))
            logger.debug('total carryover h2 items:{}'.format(cursor.rowcount))
    except:
        raise

def carryover_sched_b_payments(cmte_id, report_id, parent_id, current_id):
    """
    do carryover on sched_b debt payments
    -- Deprecated
    """
    _sql = """
    INSERT INTO public.sched_b(
        cmte_id, report_id, line_number, transaction_type, 
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
            aggregate_amt,
            create_date
					)
    SELECT cmte_id, %s, line_number, transaction_type, 
            get_next_transaction_id('SB'), %s, back_ref_sched_name, 
            entity_id, expenditure_date, expenditure_amount, 
            semi_annual_refund_bundled_amount, expenditure_purpose, 
            category_code, memo_code, memo_text, election_code, 
            election_other_description, beneficiary_cmte_id, 
            other_name, other_street_1, 
            other_street_2, other_city, other_state, other_zip, 
            nc_soft_account, transaction_type_identifier, 
            beneficiary_cmte_name,
            beneficiary_cand_entity_id,
            aggregate_amt,
            now()
    FROM public.sched_b 
    WHERE cmte_id = %s 
    AND back_ref_transaction_id = %s 
    AND delete_ind is distinct from 'Y'
    """
    _v = [report_id, current_id, cmte_id, parent_id]
    do_transaction(_sql, _v)
    logger.debug("sched_b carryover done.")


def do_carryover_sc_payments(cmte_id, report_id, rowcount):
    """
    -- Deprecated
    carry over all debt payment child transactions, including:
    sched_b
    sched_e
    sched_f
    sched_h4
    sched_h6
    """

    # first query the parent-child relationship in sched_d for current report
    # need this informattion for carrying over all the payments
    _sql = """
    select back_ref_transaction_id as parent_id, transaction_id as current_id 
    from public.sched_d d
    where d.cmte_id = %s
    and d.report_id = %s
    and d.delete_ind is distinct from 'Y'
    order by create_date desc, last_update_date desc
    """
    try:
        # new_beginning_balance = new_balance
        with connection.cursor() as cursor:
            cursor.execute(_sql, [cmte_id, report_id])
            for i in range(rowcount):
                parent_id = cursor.fetchone()[0]
                current_id = cursor.fetchone()[1]
                carryover_sched_b_payments(
                    cmte_id, report_id, parent_id, current_id)
                # carryover_sched_e_payments(cmte_id, report_id, parent_id, current_id)
                # carryover_sched_f_payments(cmte_id, report_id, parent_id, current_id)
                # carryover_sched_h4_payments(cmte_id, report_id, parent_id, current_id)
                # carryover_sched_h6_payments(cmte_id, report_id, parent_id, current_id)
    except:
        raise
