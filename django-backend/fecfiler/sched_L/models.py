from django.db import models

# Create your models here.
# sched_L table

"""
  record_id
  account_name
  cvg_from_date
  cvg_end_date
  item_receipts
  unitem_receipts
  ttl_receipts
  other_receipts
  total_receipts
  voter_reg_disb_amount
  voter_id_disb_amount
  gotv_disb_amount
  generic_campaign_disb_amount
  total_disb_sub
  other_disb
  total_disb
  coh_bop
  receipts
  subtotal
  disbursements
  coh_cop
  item_receipts_ytd
  unitem_receipts_ytd
  total_reciepts_ytd
  other_receipts_ytd
  total_receipts_ytd
  voter_reg_disb_amount_ytd
  voter_id_disb_amount_ytd
  gotv_disb_amount_ytd
  generic_campaign_disb_amount_ytd
  total_disb_sub_ytd
  other_disb_ytd
  total_disb_ytd
  coh_coy
  receipts_ytd
  sub_total_ytd
  disbursements_ytd
  coh_cop_ytd

  delete_ind
  create_date
  last_update_date
"""


class SchedL(models.Model):
    cmte_id = models.CharField(max_length=9)
    report_id = models.BigIntegerField()
    transaction_type_identifier = models.CharField(
        max_length=12, blank=True, null=True)
    transaction_id = models.CharField(primary_key=True, max_length=20)
    record_id = models.CharField(max_length=90)
    account_name = models.CharField(max_length=20)
    cvg_from_date = models.DateField(blank=True, null=True)
    cvg_end_date = models.DateField(blank=True, null=True)
    item_receipts = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True)
    unitem_receipts = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True)
    ttl_receipts = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True)
    other_receipts = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True)
    total_receipts = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True)
    voter_reg_disb_amount = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True)
    voter_id_disb_amount = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True)
    gotv_disb_amount = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True)
    generic_campaign_disb_amount = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True)
    total_disb_sub = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True)
    other_disb = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True)
    total_disb = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True)
    coh_bop = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True)
    receipts = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True)
    subtotal = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True)
    disbursements = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True)
    coh_cop = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True)
    item_receipts_ytd = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True)
    unitem_receipts_ytd = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True)
    total_reciepts_ytd = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True)
    other_receipts_ytd = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True)
    total_receipts_ytd = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True)
    voter_reg_disb_amount_ytd = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True)
    voter_id_disb_amount_ytd = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True)
    gotv_disb_amount_ytd = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True)
    generic_campaign_disb_amount_ytd = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True)
    total_disb_sub_ytd = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True)
    other_disb_ytd = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True)
    total_disb_ytd = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True)
    coh_coy = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True)
    receipts_ytd = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True)
    sub_total_ytd = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True)
    disbursements_ytd = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True)
    coh_cop_ytd = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True)
    delete_ind = models.CharField(max_length=1, blank=True, null=True)
    create_date = models.DateTimeField(blank=True, null=True)
    last_update_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'sched_l'
