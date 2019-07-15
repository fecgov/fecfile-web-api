from django.db import models

# Schedule D, it shows debts and obligations owed to or by the committee that are required to be disclosed.

"""
CREATE TABLE public.sched_d
(
    cmte_id character varying(9) COLLATE pg_catalog."default" NOT NULL,
    report_id bigint NOT NULL,
    transaction_type_identifier character varying(12) COLLATE pg_catalog."default",
    transaction_id character varying(20) COLLATE pg_catalog."default" NOT NULL DEFAULT get_next_transaction_id('SC2'::bpchar),
    creditor_entity_id character varying(20) COLLATE pg_catalog."default",
    purpose character varying(100) COLLATE pg_catalog."default",
    beginning_balance numeric(12,2),
    incurred_amount numeric(12,2),
    payment_amount numeric(12,2),
    balance_at_close numeric(12,2),
    delete_ind character(1) COLLATE pg_catalog."default",
    create_date timestamp without time zone DEFAULT now(),
    last_update_date timestamp without time zone DEFAULT now(),
    CONSTRAINT sched_d_transaction_id_pk PRIMARY KEY (transaction_id)
)
"""