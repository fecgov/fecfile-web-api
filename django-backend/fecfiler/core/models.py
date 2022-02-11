from django.db import models


class Cmte_Report_Types_View(models.Model):  # noqa N801
    cmte_id = models.CharField(max_length=9)
    filing_freq = models.CharField(max_length=1, blank=True, null=True)
    form_type = models.CharField(max_length=10)
    report_type = models.CharField(max_length=10)
    rpt_type_desc = models.CharField(max_length=200, blank=True, null=True)
    regular_special_report_ind = models.CharField(max_length=3, blank=True, null=True)
    rpt_type_info = models.CharField(max_length=200, blank=True, null=True)
    rpt_type_order = models.IntegerField(blank=True, null=True)
    cvg_start_date = models.DateField(blank=True, null=True)
    cvg_end_date = models.DateField(blank=True, null=True)
    due_date = models.DateField(blank=True, null=True)

    class Meta:
        unique_together = (("cmte_id", "form_type", "report_type"),)


class My_Forms_View(models.Model):  # noqa N801
    cmte_id = models.CharField(primary_key=True, max_length=9)
    category = models.CharField(max_length=25)
    form_type = models.CharField(max_length=10)
    due_date = models.DateField(blank=True, null=True)
    form_description = models.CharField(max_length=300, blank=True, null=True)
    form_info = models.CharField(max_length=1000, blank=True, null=True)


class Filing_Notification(models.Model):  # noqa N801
    notification_id = models.BigIntegerField(primary_key=True)
    cmte_id = models.CharField(max_length=9)
    notification_type = models.CharField(max_length=100)
    sent_date = models.DateTimeField(null=True, blank=True)
    message_subject = models.CharField(max_length=500)
    message_body = models.TextField()
