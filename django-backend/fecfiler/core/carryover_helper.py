import logging

from django.db import connection

from fecfiler.core.transaction_util import do_transaction

logger = logging.getLogger(__name__)


def get_next_transaction_id(trans_char):
    """get next transaction_id with seeding letter, like 'SA'"""
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """SELECT public.get_next_transaction_id(%s)""", [trans_char]
            )
            transaction_id = cursor.fetchone()[0]
        return transaction_id
    except Exception:
        raise


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
    except BaseException:
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
                return cursor.fetchone()[0] == "PTY"
        return False
    except BaseException:
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
                logger.debug("no h1 found in current report. need carryover:")
                cursor.execute(carryover_sql, (report_id, cmte_id))
                if cursor.rowcount != 1:
                    logger.debug("no valid h1 found for carryover.")
            logger.debug("pty h1 carryover done.")
    except BaseException:
        raise


def do_pac_h1_carryover(cmte_id, report_id):
    """
    check if there is outstanding h1 item exist or not:
    if yes:
        do carryover
    else:
        no carryover
    after carryover, the carryover h1 will become child of the parent h1

    outstanding h1: non-parent h1(back_ref_transaction_id is null)
    also, need to check report date and only do forward carryover
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
                and t.delete_ind is distinct from 'Y'
            )
            AND h.delete_ind is distinct from 'Y'
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(carryover_sql, (report_id, cmte_id, report_id, cmte_id))
            logger.debug(
                "pac h1 carryover done, carryover items:{}".format(cursor.rowcount)
            )
    except BaseException:
        raise


# this one is deprecated
def do_h1_carryover(cmte_id, report_id):
    """
    doing h1 carryover: deprecated
    """
    logger.debug(
        "doing h1 caryover with cmte_id {} and report_id {}".format(cmte_id, report_id)
    )

    _sql = """
    SELECT extract(day from cvg_start_date) as d,
    extract(month from cvg_start_date) as m
    FROM public.reports
    WHERE report_id = %s and cmte_id = %s
    """
    with connection.cursor() as cursor:
        # cursor.execute(count_sql, (report_id, cmte_id, report_id, cmte_id))
        # if cursor.rowcount == 0:
        cursor.execute(_sql, (report_id, cmte_id))
        if cursor.rowcount:
            _res = cursor.fetchone()
            if int(_res[0]) == 1 and int(_res[1] == 1):
                logger.debug("new year report, no h1 carryover needed.")
                return

    # if is_pty(cmte_id):
    #     logger.debug('party h1 carryover...')
    #     do_pty_h1_carryover(cmte_id, report_id)
    if is_pac(cmte_id):
        logger.debug("pac h1 carryover...")
        do_pac_h1_carryover(cmte_id, report_id)
    else:
        pass


def do_h2_carryover(cmte_id, report_id):
    """
    this is the function to handle h2 carryover form one report to next report:
    1. load all h2 items with distinct event names from last report
    2. update all records with new transaction_id, new report_id
    3. set ratio code to 's' - same as previously
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
                and h2.delete_ind is distinct from 'Y'
            )
            AND h.delete_ind is distinct from 'Y'
    """
    try:
        logger.debug("doing h2 carryover...")
        with connection.cursor() as cursor:
            cursor.execute(_sql, (report_id, cmte_id, report_id, report_id, cmte_id))
            if cursor.rowcount == 0:
                logger.debug("No valid h2 items found.")
            logger.debug("h2 carryover done with report_id {}".format(report_id))
            logger.debug("total carryover h2 items:{}".format(cursor.rowcount))
    except BaseException:
        raise


def do_loan_carryover(cmte_id, report_id):
    """
    this is the function to handle loan carryover form one report to next report:
    1. duplicate and carryover all loans:
    - non-zero loan_balance
    - outstanding and dangled(not carried over before)
    - loan report date < current report coverge start(forward carryover only)

    2. update all records with new transaction_id, new report_id
    3. set new loan back_ref_transaction_id to parent transaction_id
    """
    _sql = """
    insert into public.sched_c(
                    cmte_id,
                    report_id,
                    line_number,
                    transaction_type,
                    transaction_type_identifier,
                    transaction_id,
                    entity_id,
                    election_code,
                    election_other_description,
                    loan_amount_original,
                    loan_payment_to_date,
                    loan_balance,
                    loan_incurred_date,
                    loan_due_date,
                    loan_intrest_rate,
                    is_loan_secured,
                    is_personal_funds,
                    lender_cmte_id,
                    lender_cand_id,
                    lender_cand_last_name,
                    lender_cand_first_name,
                    lender_cand_middle_name,
                    lender_cand_prefix,
                    lender_cand_suffix,
                    lender_cand_office,
                    lender_cand_state,
                    lender_cand_district,
                    memo_code,
                    memo_text,
                    back_ref_transaction_id,
                    create_date
                    )
                    SELECT
                    c.cmte_id,
                    %s,
                    c.line_number,
                    '',
                    c.transaction_type_identifier,
                    get_next_transaction_id('SC'),
                    c.entity_id,
                    c.election_code,
                    c.election_other_description,
                    c.loan_amount_original,
                    c.loan_payment_to_date,
                    c.loan_balance,
                    c.loan_incurred_date,
                    c.loan_due_date,
                    c.loan_intrest_rate,
                    c.is_loan_secured,
                    c.is_personal_funds,
                    c.lender_cmte_id,
                    c.lender_cand_id,
                    c.lender_cand_last_name,
                    c.lender_cand_first_name,
                    c.lender_cand_middle_name,
                    c.lender_cand_prefix,
                    c.lender_cand_suffix,
                    c.lender_cand_office,
                    c.lender_cand_state,
                    c.lender_cand_district,
                    c.memo_code,
                    c.memo_text,
                    c.transaction_id,
                    now()
            FROM public.sched_c c, public.reports r
            WHERE
            c.cmte_id = %s
            AND c.loan_balance > 0
            AND c.report_id != %s
            AND c.report_id = r.report_id
            AND r.cvg_start_date < (
                        SELECT r.cvg_start_date
                        FROM   public.reports r
                        WHERE  r.report_id = %s
                    )
            AND c.transaction_id NOT In (
                select distinct back_ref_transaction_id from public.sched_c
                where cmte_id = %s
                and back_ref_transaction_id is not null
            )
            AND c.delete_ind is distinct from 'Y'
    """
    # query_back_sql = """
    # select d.back_ref_transaction_id
    # """
    logger.debug("doing loan carryover...")
    try:
        with connection.cursor() as cursor:
            cursor.execute(_sql, (report_id, cmte_id, report_id, report_id, cmte_id))
            if cursor.rowcount == 0:
                logger.debug("No carryover happens.")
            else:
                logger.debug("loan carryover done with report_id {}".format(report_id))
                logger.debug("total carryover loans:{}".format(cursor.rowcount))
                # do_carryover_sc_payments(cmte_id, report_id, cursor.rowcount)
        logger.debug("carryover done.")
    except BaseException:
        raise


def do_levin_carryover(cmte_id, report_id):
    """
    carryover sched_l item for levin account
    ending cash_on_hand become the beginning cash_on_hand of current report
    """
    _sql = """
       insert into public.sched_l(
                    cmte_id,
                    report_id,
                    record_id,
                    account_name,
                    line_number,
                    transaction_type_identifier,
                    transaction_id,
                    coh_bop,
                    coh_cop,
                    create_date,
                    cvg_from_date,
                    cvg_end_date
                    )
                    SELECT
                    d.cmte_id,
                    %s,
                    d.record_id,
                    d.account_name,
                    d.line_number,
                    d.transaction_type_identifier,
                    get_next_transaction_id('SL'),
                    d.coh_cop,
                    d.coh_cop,
                    now(),
                    r2.cvg_start_date,
                    r2.cvg_end_date
            FROM public.sched_l d, public.reports r1, public.reports r2
            WHERE
            d.cmte_id = %s
            AND d.report_id = r1.report_id
            AND DATE_PART('day', r2.cvg_start_date::timestamp - r1.cvg_end_date::timestamp) = 1
            AND r2.report_id = %s
            AND d.delete_ind is distinct from 'Y';
    """
    # query_back_sql = """
    # select d.back_ref_transaction_id
    # """
    logger.debug("doing levin carryover...")
    try:
        with connection.cursor() as cursor:
            cursor.execute(_sql, (report_id, cmte_id, report_id))
            if cursor.rowcount == 0:
                logger.debug("No carryover happens.")
            else:
                logger.debug(
                    "levin acct carryover done with report_id {}".format(report_id)
                )
                logger.debug("total carryover levin summary:{}".format(cursor.rowcount))
                # do_carryover_sc_payments(cmte_id, report_id, cursor.rowcount)
                logger.debug("carryover done.")
    except BaseException:
        raise


def do_debt_carryover(cmte_id, report_id):
    """
    this is the function to handle debt carryover form one report to next report:
    1. load all non-zero close_balance sched_d and make sure:
    - debt incurred date < report coverge start
    - only load non-parent items

    2. update all records with new transaction_id, new report_id
    3. copy close_balance to starting_balance, leave all other amount 0
    4. insert sched_c into db
    """
    _sql = """
    insert into public.sched_d(
                    cmte_id,
                    report_id,
                    line_num,
                    transaction_type_identifier,
                    transaction_id,
                    entity_id,
                    beginning_balance,
                    balance_at_close,
                    incurred_amount,
                    payment_amount,
                    purpose,
                    back_ref_transaction_id,
                    create_date
                    )
                    SELECT
                    d.cmte_id,
                    %s,
                    d.line_num,
                    d.transaction_type_identifier,
                    get_next_transaction_id('SD'),
                    d.entity_id,
                    d.balance_at_close,
                    d.balance_at_close,
                    0,
                    0,
                    d.purpose,
                    d.transaction_id,
                    now()
            FROM public.sched_d d, public.reports r
            WHERE
            d.cmte_id = %s
            AND d.balance_at_close > 0
            AND d.report_id != %s
            AND d.report_id = r.report_id
            AND r.cvg_start_date < (
                        SELECT r.cvg_start_date
                        FROM   public.reports r
                        WHERE  r.report_id = %s
                    )
            AND d.transaction_id NOT In (
                select distinct d1.back_ref_transaction_id from public.sched_d d1
                where d1.cmte_id = %s
                and d1.back_ref_transaction_id is not null
                and d1.delete_ind is distinct from 'Y'
            )
            AND d.delete_ind is distinct from 'Y' ;
    """
    # query_back_sql = """
    # select d.back_ref_transaction_id
    # """
    logger.debug("doing debt carryover...")
    try:
        with connection.cursor() as cursor:
            cursor.execute(_sql, (report_id, cmte_id, report_id, report_id, cmte_id))
            if cursor.rowcount == 0:
                logger.debug("No carryover happens.")
            else:
                logger.debug("debt carryover done with report_id {}".format(report_id))
                logger.debug("total carryover debts:{}".format(cursor.rowcount))
                # do_carryover_sc_payments(cmte_id, report_id, cursor.rowcount)
                logger.debug("carryover done.")
    except BaseException:
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
                carryover_sched_b_payments(cmte_id, report_id, parent_id, current_id)
                # carryover_sched_e_payments(cmte_id, report_id, parent_id, current_id)
                # carryover_sched_f_payments(cmte_id, report_id, parent_id, current_id)
                # carryover_sched_h4_payments(cmte_id, report_id, parent_id, current_id)
                # carryover_sched_h6_payments(cmte_id, report_id, parent_id, current_id)
    except BaseException:
        raise


def do_in_between_report_carryover(cmte_id, report_id):
    try:
        logger.debug("inside do_in_between_report_carryover function...")
        _sql = """SELECT r.report_id FROM public.reports r WHERE r.cmte_id = %s AND r.cvg_start_date >
                  (SELECT pr.cvg_end_date FROM public.reports pr WHERE pr.cmte_id = %s AND pr.report_id = %s)
                  AND r.delete_ind IS DISTINCT FROM 'Y' ORDER BY r.cvg_start_date ASC LIMIT 1"""
        _values = [cmte_id, cmte_id, report_id]
        with connection.cursor() as cursor:
            cursor.execute(_sql, _values)
            next_report_id = cursor.fetchone()
            if next_report_id:
                next_report_id = next_report_id[0]
                logger.debug("found future report id {}".format(next_report_id))
            else:
                logger.debug("No future report found")
        if next_report_id:
            _sql1 = """SELECT transaction_id FROM public.sched_c WHERE report_id = %s AND cmte_id = %s
                    AND delete_ind IS DISTINCT FROM 'Y' """
            _values1 = [str(next_report_id), cmte_id]
            with connection.cursor() as cursor:
                cursor.execute(_sql1, _values1)
                next_transaction_id_list = cursor.fetchall()
            if next_transaction_id_list:
                logger.debug(
                    "found loans in future report id: {}".format(next_report_id)
                )
            else:
                logger.debug(
                    "No loan transactions found in future report id: {}".format(
                        next_report_id
                    )
                )
            for next_transaction_id in next_transaction_id_list:
                next_transaction_id = next_transaction_id[0]
                this_report_transaction_id = get_next_transaction_id("SC")
                _sql2 = """INSERT INTO public.sched_c(cmte_id, report_id, line_number, transaction_type,
                      transaction_type_identifier, transaction_id, entity_id, election_code, election_other_description,
                      loan_amount_original, loan_payment_to_date, loan_balance, loan_incurred_date, loan_due_date,
                      loan_intrest_rate, is_loan_secured, is_personal_funds, lender_cmte_id, lender_cand_id,
                      lender_cand_last_name, lender_cand_first_name, lender_cand_middle_name, lender_cand_prefix,
                      lender_cand_suffix, lender_cand_office, lender_cand_state, lender_cand_district, memo_code,
                      memo_text, back_ref_transaction_id,create_date)
                        SELECT c.cmte_id, %s, c.line_number, '',
                        c.transaction_type_identifier, %s, c.entity_id, c.election_code, c.election_other_description,
                        c.loan_amount_original, c.loan_payment_to_date, c.loan_balance, c.loan_incurred_date, c.loan_due_date,
                        c.loan_intrest_rate, c.is_loan_secured, c.is_personal_funds, c.lender_cmte_id, c.lender_cand_id,
                        c.lender_cand_last_name, c.lender_cand_first_name, c.lender_cand_middle_name, c.lender_cand_prefix,
                        c.lender_cand_suffix, c.lender_cand_office, c.lender_cand_state, c.lender_cand_district, c.memo_code,
                        c.memo_text, c.back_ref_transaction_id, now()
                        FROM public.sched_c c
                        WHERE c.cmte_id = %s
                        AND c.report_id = %s AND c.transaction_id = %s
                        AND c.delete_ind is distinct from 'Y'"""
                _values2 = [
                    report_id,
                    this_report_transaction_id,
                    cmte_id,
                    next_report_id,
                    next_transaction_id,
                ]

                _sql3 = """UPDATE public.sched_c SET back_ref_transaction_id = %s WHERE cmte_id = %s
                        AND report_id = %s AND transaction_id = %s
                        AND delete_ind is distinct from 'Y'"""
                _values3 = [
                    this_report_transaction_id,
                    cmte_id,
                    next_report_id,
                    next_transaction_id,
                ]

                with connection.cursor() as cursor:
                    cursor.execute(_sql2, _values2)
                    if cursor.rowcount == 0:
                        logger.debug(
                            "could NOT create duplicate transaction for transaction id: {}".format(
                                next_transaction_id
                            )
                        )
                    else:
                        logger.debug(
                            "created duplicate transaction for transaction id: {}. New transaction id: {}".format(
                                next_transaction_id, this_report_transaction_id
                            )
                        )
                    cursor.execute(_sql3, _values3)
                    if cursor.rowcount == 0:
                        logger.debug(
                            "could NOT update back_ref_transaction_id for transaction id: {} with id: {}".format(
                                next_transaction_id, this_report_transaction_id
                            )
                        )
                    else:
                        logger.debug(
                            "updated back_ref_transaction_id for transaction id: {} with id: {}".format(
                                next_transaction_id, this_report_transaction_id
                            )
                        )
                logger.debug("done with transaction id: {}".format(next_transaction_id))
            logger.debug("loans carryover done...")

            _sql4 = """SELECT transaction_id FROM public.sched_d WHERE report_id = %s AND cmte_id = %s
                  AND delete_ind IS DISTINCT FROM 'Y'"""
            _values4 = [str(next_report_id), cmte_id]
            with connection.cursor() as cursor:
                cursor.execute(_sql4, _values4)
                next_debt_transaction_id_list = cursor.fetchall()
            if next_debt_transaction_id_list:
                logger.debug(
                    "found debts in future report id: {}.".format(next_report_id)
                )
            else:
                logger.debug(
                    "No debt transactions found in future report id: {}".format(
                        next_report_id
                    )
                )
            for next_transaction_id in next_debt_transaction_id_list:
                next_transaction_id = next_transaction_id[0]
                this_report_transaction_id = get_next_transaction_id("SD")
                _sql5 = """INSERT INTO public.sched_d(cmte_id, report_id, line_num, transaction_type_identifier,
                      transaction_id, entity_id, beginning_balance, balance_at_close, incurred_amount,
                      payment_amount, purpose, back_ref_transaction_id, create_date)
                        SELECT d.cmte_id, %s, d.line_num, d.transaction_type_identifier,
                        %s, d.entity_id, d.beginning_balance, d.beginning_balance, 0,
                        0, d.purpose, d.back_ref_transaction_id, now()
                        FROM public.sched_d d
                        WHERE d.cmte_id = %s
                        AND d.report_id = %s AND d.transaction_id = %s
                        AND d.delete_ind is distinct from 'Y'"""
                _values5 = [
                    report_id,
                    this_report_transaction_id,
                    cmte_id,
                    next_report_id,
                    next_transaction_id,
                ]

                _sql6 = """UPDATE public.sched_d SET back_ref_transaction_id = %s WHERE cmte_id = %s
                        AND report_id = %s AND transaction_id = %s
                        AND delete_ind is distinct from 'Y'"""
                _values6 = [
                    this_report_transaction_id,
                    cmte_id,
                    next_report_id,
                    next_transaction_id,
                ]

                with connection.cursor() as cursor:
                    cursor.execute(_sql5, _values5)
                    if cursor.rowcount == 0:
                        logger.debug(
                            "could NOT create duplicate transaction for transaction id: {}".format(
                                next_transaction_id
                            )
                        )
                    else:
                        logger.debug(
                            "created duplicate transaction for transaction id: {}. New transaction id: {}".format(
                                next_transaction_id, this_report_transaction_id
                            )
                        )
                    cursor.execute(_sql6, _values6)
                    if cursor.rowcount == 0:
                        logger.debug(
                            "could NOT update back_ref_transaction_id for transaction id: {} with id: {}".format(
                                next_transaction_id, this_report_transaction_id
                            )
                        )
                    else:
                        logger.debug(
                            "updated back_ref_transaction_id for transaction id: {} with id: {}".format(
                                next_transaction_id, this_report_transaction_id
                            )
                        )
                logger.debug("done with transaction id: {}".format(next_transaction_id))
            logger.debug("debts carryover done...")
    except Exception as e:
        raise Exception(
            "The do_in_between_report_carryover function is throwing an error: "
            + str(e)
        )
