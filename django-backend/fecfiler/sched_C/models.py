from django.db import models

# Create your models here.
# sched_C has three different models: loans, endorsements and loan guarantees a committee
# The committee continues to report the loan until it is repaid.

# sched_c table
"""
CREATE TABLE public.sched_c
(
    cmte_id character varying(9) COLLATE pg_catalog."default" NOT NULL,
    report_id bigint NOT NULL,
    line_number character varying(8) COLLATE pg_catalog."default" NOT NULL,
    transaction_type character varying(12) COLLATE pg_catalog."default" NOT NULL,
    transaction_type_identifier character varying(12) COLLATE pg_catalog."default",
    transaction_id character varying(20) COLLATE pg_catalog."default" NOT NULL DEFAULT get_next_transaction_id('SC'::bpchar),
    entity_id character varying(20) COLLATE pg_catalog."default",
    election_code character varying(5) COLLATE pg_catalog."default",
    election_other_description character varying(20) COLLATE pg_catalog."default",
    loan_amount_original numeric(12,2),
    loan_payment_to_date numeric(12,2),
    loan_balance numeric(12,2),
    loan_incurred_date date,
    loan_due_date character varying(15) COLLATE pg_catalog."default",
    loan_intrest_rate character varying(15) COLLATE pg_catalog."default",
    is_loan_secured character(1) COLLATE pg_catalog."default",
    is_personal_funds character(1) COLLATE pg_catalog."default",
    lender_cmte_id character varying(9) COLLATE pg_catalog."default",
    lender_cand_id character varying(9) COLLATE pg_catalog."default",
    lender_cand_last_name character varying(30) COLLATE pg_catalog."default",
    lender_cand_first_name character varying(20) COLLATE pg_catalog."default",
    lender_cand_middle_name character varying(20) COLLATE pg_catalog."default",
    lender_cand_prefix character varying(10) COLLATE pg_catalog."default",
    lender_cand_suffix character varying(10) COLLATE pg_catalog."default",
    lender_cand_office character varying(1) COLLATE pg_catalog."default",
    lender_cand_state character varying(2) COLLATE pg_catalog."default",
    lender_cand_district numeric,
    memo_code character varying(1) COLLATE pg_catalog."default",
    memo_text character varying(100) COLLATE pg_catalog."default",
    delete_ind character(1) COLLATE pg_catalog."default",
    create_date timestamp without time zone DEFAULT now(),
    last_update_date timestamp without time zone DEFAULT now(),
    CONSTRAINT sched_c_transaction_id_pk PRIMARY KEY (transaction_id)
)
"""

# sched_c1
"""
CREATE TABLE public.sched_c1
(
    cmte_id character varying(9) COLLATE pg_catalog."default" NOT NULL,
    report_id bigint NOT NULL,
    line_number character varying(8) COLLATE pg_catalog."default" NOT NULL,
    transaction_type character varying(12) COLLATE pg_catalog."default" NOT NULL,
    transaction_type_identifier character varying(12) COLLATE pg_catalog."default",
    transaction_id character varying(20) COLLATE pg_catalog."default" NOT NULL DEFAULT get_next_transaction_id('SC1'::bpchar),
    lender_entity_id character varying(20) COLLATE pg_catalog."default",
    loan_amount numeric(12,2),
    loan_intrest_rate character varying(15) COLLATE pg_catalog."default",
    loan_incurred_date date,
    loan_due_date date,
    is_loan_restructured character varying(1) COLLATE pg_catalog."default",
    original_loan_date date,
    credit_amount_this_draw numeric(12,2),
    total_outstanding_balance numeric(12,2),
    other_parties_liable character varying(1) COLLATE pg_catalog."default",
    pledged_collateral_ind character varying(1) COLLATE pg_catalog."default",
    pledge_collateral_desc character varying(100) COLLATE pg_catalog."default",
    pledge_collateral_amount numeric(12,2),
    perfected_intrest_ind character varying(1) COLLATE pg_catalog."default",
    future_income_ind character varying(1) COLLATE pg_catalog."default",
    future_income_desc character varying(100) COLLATE pg_catalog."default",
    future_income_estimate numeric(12,2),
    depository_account_established_date date,
    depository_account_location character varying(200) COLLATE pg_catalog."default",
    depository_account_street_1 character varying(34) COLLATE pg_catalog."default",
    depository_account_street_2 character varying(34) COLLATE pg_catalog."default",
    depository_account_city character varying(30) COLLATE pg_catalog."default",
    depository_account_state character varying(2) COLLATE pg_catalog."default",
    depository_account_zip character varying(9) COLLATE pg_catalog."default",
    depository_account_auth_date date,
    basis_of_loan_desc character varying(100) COLLATE pg_catalog."default",
    treasurer_entity_id character varying(20) COLLATE pg_catalog."default",
    treasurer_signed_date date,
    authorized_entity_id character varying(20) COLLATE pg_catalog."default",
    authorized_entity_title character varying(20) COLLATE pg_catalog."default",
    authorized_signed_date date,
    delete_ind character(1) COLLATE pg_catalog."default",
    create_date timestamp without time zone DEFAULT now(),
    last_update_date timestamp without time zone DEFAULT now(),
    CONSTRAINT sched_c1_transaction_id_pk PRIMARY KEY (transaction_id)
)
"""

# sched_c2
"""
CREATE TABLE public.sched_c2
(
    cmte_id character varying(9) COLLATE pg_catalog."default" NOT NULL,
    report_id bigint NOT NULL,
    transaction_type_identifier character varying(12) COLLATE pg_catalog."default",
    transaction_id character varying(20) COLLATE pg_catalog."default" NOT NULL DEFAULT get_next_transaction_id('SC2'::bpchar),
    guarantor_entity_id character varying(20) COLLATE pg_catalog."default",
    guaranteed_amount numeric(12,2),
    delete_ind character(1) COLLATE pg_catalog."default",
    create_date timestamp without time zone DEFAULT now(),
    last_update_date timestamp without time zone DEFAULT now(),
    CONSTRAINT sched_c2_transaction_id_pk PRIMARY KEY (transaction_id)
)
"""
