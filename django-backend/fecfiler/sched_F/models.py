from django.db import models

# Create your models here.
# sched_F table


class SchedF(models.Model):
    cmte_id = models.CharField(max_length=9)
    report_id = models.BigIntegerField()
    transaction_type_identifier = models.CharField(
        max_length=12, blank=True, null=True)
    transaction_id = models.CharField(primary_key=True, max_length=20)
    back_ref_transaction_id = models.CharField(max_length=20)
    back_ref_sched_name = models.CharField(max_length=8)
    coordinated_exp_ind = models.CharField(max_length=3)
    designating_cmte_id = models.CharField(max_length=9)
    designating_cmte_name = models.CharField(max_length=200)
    subordinate_cmte_id = models.CharField(max_length=9)
    subordinate_cmte_name = models.CharField(max_length=200)
    subordinate_cmte_street_1 = models.CharField(max_length=34)
    subordinate_cmte_street_2 = models.CharField(max_length=34)
    subordinate_cmte_city = models.CharField(max_length=30)
    subordinate_cmte_state = models.CharField(max_length=2)
    subordinate_cmte_zip = models.CharField(max_length=10)
    payee_entity_id = models.CharField(max_length=20)
    expenditure_date = models.DateField(blank=True, null=True)
    expenditure_amount = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True)
    aggregate_general_elec_exp = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True)
    purpose = models.CharField(max_length=100)
    category_code = models.CharField(max_length=3)
    payee_cmte_id = models.CharField(max_length=9)
    payee_cand_id = models.CharField(max_length=9)
    payee_cand_last_name = models.CharField(max_length=30)
    payee_cand_fist_name = models.CharField(max_length=20)
    payee_cand_middle_name = models.CharField(max_length=20),
    payee_cand_prefix = models.CharField(max_length=10)
    payee_cand_suffix = models.CharField(max_length=10)
    payee_cand_office = models.CharField(max_length=1)
    payee_cand_state = models.CharField(max_length=2)
    payee_cand_district = models.CharField(max_length=2)
    memo_code = models.CharField(max_length=1, blank=True, null=True)
    memo_text = models.CharField(max_length=90, blank=True, null=True)
    delete_ind = models.CharField(max_length=1, blank=True, null=True)
    create_date = models.DateTimeField(blank=True, null=True)
    last_update_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'sched_F'
