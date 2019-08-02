from django.db import models

# Create your models here.
# sched_H table
"""
CREATE TABLE public.sched_h3
(
  cmte_id character varying(9) NOT NULL,
  report_id bigint NOT NULL,
  transaction_type_identifier character varying(12),
  transaction_id character varying(20) NOT NULL DEFAULT get_next_transaction_id('H3'::bpchar),
  back_ref_transaction_id character varying(20),
  back_ref_sched_name character varying(8),
  account_name character varying(90),
  activity_event_type character varying(2),
  activity_event_name character varying(90),
  receipt_date date,
  total_amount_transferred numeric(12,2),
  transferred_amount numeric(12,2),
  memo_code character varying(1),
  memo_text character varying(90),
  delete_ind character(1),
  create_date timestamp without time zone DEFAULT now(),
  last_update_date timestamp without time zone DEFAULT now(),
  CONSTRAINT sched_h3_transaction_id_pk PRIMARY KEY (transaction_id)
)
"""


class SchedH3(models.Model):
    cmte_id = models.CharField(max_length=9)
    report_id = models.BigIntegerField()
    transaction_type_identifier = models.CharField(
        max_length=12, blank=True, null=True)
    transaction_id = models.CharField(primary_key=True, max_length=20)
    back_ref_transaction_id = models.CharField(primary_key=True, max_length=9)
    back_ref_sched_name = models.CharField(primary_key=True, max_length=20)
    account_name = models.CharField(primary_key=True, max_length=90)
    activity_event_type = models.CharField(primary_key=True, max_length=2)
    activity_event_name = models.CharField(primary_key=True, max_length=90)
    receipt_date = models.DateField(blank=True, null=True)
    total_amount_transferred = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True)
    transferred_amount = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True)
    memo_code = models.CharField(max_length=1, blank=True, null=True)
    memo_text = models.CharField(max_length=90, blank=True, null=True)
    delete_ind = models.CharField(max_length=1, blank=True, null=True)
    create_date = models.DateTimeField(blank=True, null=True)
    last_update_date = models.DateTimeField(blank=True, null=True)


    class Meta:
        managed = False
        db_table = 'sched_h3'



