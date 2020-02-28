from django.db import models

# Create your models here.
# sched_H3 table
# sched_H4 table
# sched_H5 table


class SchedH3(models.Model):
    cmte_id = models.CharField(max_length=9)
    report_id = models.BigIntegerField()
    transaction_type_identifier = models.CharField(
        max_length=12, blank=True, null=True)
    transaction_id = models.CharField(primary_key=True, max_length=20)
    back_ref_transaction_id = models.CharField(max_length=20)
    back_ref_sched_name = models.CharField(max_length=8)
    account_name = models.CharField(max_length=90)
    activity_event_type = models.CharField(max_length=2)
    activity_event_name = models.CharField(max_length=90)
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


class SchedH4(models.Model):
    cmte_id = models.CharField(max_length=9)
    report_id = models.BigIntegerField()
    transaction_type_identifier = models.CharField(
        max_length=12, blank=True, null=True)
    transaction_id = models.CharField(primary_key=True, max_length=20)
    back_ref_transaction_id = models.CharField(max_length=20)
    back_ref_sched_name = models.CharField(max_length=8)
    payee_entity_id = models.CharField(max_length=20)
    activity_event_identifier = models.CharField(max_length=90)
    expenditure_date = models.DateField(blank=True, null=True)
    fed_share_amount = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True)
    non_fed_share_amount = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True)
    total_amount = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True)
    activity_event_amount = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True)
    purpose = models.CharField(max_length=100)
    category_code = models.CharField(max_length=2)
    activity_event_type = models.CharField(max_length=2)
    memo_code = models.CharField(max_length=1, blank=True, null=True)
    memo_text = models.CharField(max_length=90, blank=True, null=True)
    delete_ind = models.CharField(max_length=1, blank=True, null=True)
    create_date = models.DateTimeField(blank=True, null=True)
    last_update_date = models.DateTimeField(blank=True, null=True)


    class Meta:
        managed = False
        db_table = 'sched_h4'



class SchedH5(models.Model):
    cmte_id = models.CharField(max_length=9)
    report_id = models.BigIntegerField()
    transaction_type_identifier = models.CharField(
        max_length=12, blank=True, null=True)
    transaction_id = models.CharField(primary_key=True, max_length=20)
    account_name = models.CharField(max_length=90)
    receipt_date = models.DateField(blank=True, null=True)
    total_amount_transferred = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True)
    voter_registration_amount = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True)
    voter_id_amount = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True)
    gotv_amount =  models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True)
    generic_campaign_amount = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True)
    memo_code = models.CharField(max_length=1, blank=True, null=True)
    memo_text = models.CharField(max_length=90, blank=True, null=True)
    delete_ind = models.CharField(max_length=1, blank=True, null=True)
    create_date = models.DateTimeField(blank=True, null=True)
    last_update_date = models.DateTimeField(blank=True, null=True)


    class Meta:
        managed = False
        db_table = 'sched_h5'



class SchedH6(models.Model):
    cmte_id = models.CharField(max_length=9)
    report_id = models.BigIntegerField()
    line_number = models.CharField(
        max_length=8, blank=True, null=True)
    transaction_type_identifier = models.CharField(
        max_length=12, blank=True, null=True)
    transaction_type=models.CharField(max_length=12)
    transaction_id = models.CharField(primary_key=True, max_length=20)
    back_ref_transaction_id = models.CharField(max_length=20)
    back_ref_sched_name = models.CharField(max_length=8)
    entity_id = models.CharField(max_length=20)
    account_event_identifier = models.CharField(max_length=90)
    expenditure_date= models.DateField(blank=True, null=True)
    total_fed_levin_amount = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True)
    federal_share = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True)
    levin_share = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True)
    activity_event_total_ytd = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True)
    expenditure_purpose = models.CharField(max_length=100)
    category_code =  models.CharField(max_length=3)
    activity_event_type =  models.CharField(max_length=20)
    memo_code = models.CharField(max_length=1, blank=True, null=True)
    memo_text = models.CharField(max_length=90, blank=True, null=True)
    delete_ind = models.CharField(max_length=1, blank=True, null=True)
    create_date = models.DateTimeField(blank=True, null=True)
    last_update_date = models.DateTimeField(blank=True, null=True)


    class Meta:
        managed = False
        db_table = 'sched_h6'











