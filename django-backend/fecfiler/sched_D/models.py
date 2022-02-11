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


class SchedD(models.Model):
    cmte_id = models.CharField(max_length=9)
    report_id = models.BigIntegerField()
    transaction_type_identifier = models.CharField(max_length=12, blank=True, null=True)
    transaction_id = models.CharField(primary_key=True, max_length=20)
    creditor_entity_id = models.CharField(max_length=20, blank=True, null=True)
    purpose = models.CharField(max_length=100, blank=True, null=True)
    beginning_balance = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True
    )
    incurred_amount = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True
    )
    payment_amount = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True
    )
    balance_at_close = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True
    )
    delete_ind = models.CharField(max_length=1, blank=True, null=True)
    create_date = models.DateTimeField(blank=True, null=True)
    last_update_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "sched_d"
