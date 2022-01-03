from django.db import models

# Create your models here.
# sched_E table


class SchedE(models.Model):
    cmte_id = models.CharField(max_length=9)
    report_id = models.BigIntegerField()
    transaction_type_identifier = models.CharField(
        max_length=12, blank=True, null=True)
    transaction_id = models.CharField(primary_key=True, max_length=20)
    back_ref_transaction_id = models.CharField(max_length=20)
    back_ref_sched_name = models.CharField(max_length=8)
    payee_entity_id = models.CharField(max_length=20)
    election_code = models.CharField(max_length=5)
    election_other_desc = models.CharField(max_length=20)
    dissemination_date = models.DateField(blank=True, null=True)
    expenditure_amount = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True)
    disbursement_date = models.DateField(blank=True, null=True)
    calendar_ytd_amount = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True)
    purpose = models.CharField(max_length=100)
    category_code = models.CharField(max_length=3)
    payee_cmte_id = models.CharField(max_length=9)
    support_oppose_code = models.CharField(max_length=1)
    so_cand_id = models.CharField(max_length=9)
    so_cand_last_name = models.CharField(max_length=30)
    so_cand_fist_name = models.CharField(max_length=20)
    so_cand_middle_name = models.CharField(max_length=20)
    so_cand_prefix = models.CharField(max_length=10)
    so_cand_suffix = models.CharField(max_length=10)
    so_cand_office = models.CharField(max_length=1)
    so_cand_district = models.CharField(max_length=2)
    so_cand_state = models.CharField(max_length=2)
    completing_entity_id = models.CharField(max_length=20)
    date_signed = models.DateField(blank=True, null=True)
    memo_code = models.CharField(max_length=1, blank=True, null=True)
    memo_text = models.CharField(max_length=90, blank=True, null=True)
    delete_ind = models.CharField(max_length=1, blank=True, null=True)
    create_date = models.DateTimeField(blank=True, null=True)
    last_update_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'sched_E'
