from django.db import models
from django.utils.translation import ugettext_lazy as _
from fecfiler.custom_storages import MediaStorage
from datetime import datetime

# Table to store F99 attachment data (Refer this documentation: https://django-db-file-storage.readthedocs.io/en/master/)


class F99Attachment(models.Model):
    bytes = models.TextField()
    filename = models.CharField(max_length=255)
    mimetype = models.CharField(max_length=50)


# added blank=True for null=True to avoid exception while saving to db.


class CommitteeInfo(models.Model):
    # Committee Information Table Model
    id = models.AutoField(primary_key=True)
    committeeid = models.CharField(max_length=9, null=False)
    committeename = models.CharField(max_length=200, null=False)
    street1 = models.CharField(max_length=34, null=False)
    street2 = models.CharField(max_length=34, null=True, blank=True)
    text = models.TextField(max_length=20000, null=False, default="-")
    reason = models.CharField(max_length=3, null=False, default="-")
    city = models.CharField(max_length=30, null=False)
    state = models.CharField(max_length=2, null=False)
    zipcode = models.TextField(null=False, max_length=9)
    treasurerlastname = models.CharField(max_length=30, null=False)
    treasurerfirstname = models.CharField(max_length=20, null=False)
    treasurermiddlename = models.CharField(max_length=20, null=True, blank=True)
    treasurerprefix = models.CharField(max_length=10, null=True, blank=True)
    treasurersuffix = models.CharField(max_length=10, null=True, blank=True)
    created_at = models.DateTimeField(null=True, default=datetime.now)
    updated_at = models.DateTimeField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    isdeleted = models.BooleanField(default=False)
    is_submitted = models.BooleanField(default=False)
    signee = models.CharField(max_length=30, null=False, default="-")
    email_on_file = models.TextField(max_length=100, null=False, default="-")
    email_on_file_1 = models.TextField(max_length=100, null=True, blank=True)
    additional_email_1 = models.TextField(max_length=100, null=True, blank=True)
    additional_email_2 = models.TextField(max_length=100, null=True, blank=True)
    filename = models.CharField(max_length=128, null=True, blank=True)
    # file = models.FileField(upload_to='forms.F99Attachment/bytes/filename/mimetype', null=True, blank=True, validators=[validate_is_pdf,])
    file = models.FileField(storage=MediaStorage(), null=True, blank=True)
    # implememted file upload using the following module: https://django-db-file-storage.readthedocs.io/en/master/
    form_type = models.CharField(max_length=3, default="F99")
    coverage_start_date = models.DateField(null=True, blank=True)
    coverage_end_date = models.DateField(null=True, blank=True)

    # class constructor
    def __unicode__(self):
        return self.committeename

    """
    def save(self, *args, **kwargs):
        delete_file_if_needed(self, 'file')
        super(CommitteeInfo, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        super(CommitteeInfo, self).delete(*args, **kwargs)
        delete_file(self, 'file')

    """

    class Meta:
        verbose_name = _("CommitteeInfo")
        verbose_name_plural = _("CommitteeInfo")


class Committee(models.Model):
    # Committee Model
    id = models.AutoField(primary_key=True)
    committeeid = models.CharField(max_length=9)
    committeename = models.CharField(max_length=200, null=False)
    street1 = models.CharField(max_length=34, null=False)
    street2 = models.CharField(max_length=34)
    city = models.CharField(max_length=30, null=False)
    state = models.CharField(max_length=2, null=False)
    zipcode = models.IntegerField(null=False)
    treasurerlastname = models.CharField(max_length=30, null=False)
    treasurerfirstname = models.CharField(max_length=20, null=False)
    treasurermiddlename = models.CharField(max_length=20)
    treasurerprefix = models.CharField(max_length=10)
    treasurersuffix = models.CharField(max_length=10)
    email_on_file = models.TextField(max_length=100, null=False, default="-")
    email_on_file_1 = models.TextField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True)
    isdeleted = models.BooleanField(default=False)

    def __unicode__(self):
        # class constructor
        return self.committeename

    class Meta:
        verbose_name = _("Committee")
        verbose_name_plural = _("Committee")


class CommitteeMaster(models.Model):
    cmte_id = models.CharField(primary_key=True, max_length=9)
    cmte_name = models.CharField(max_length=200, blank=True, null=True)
    street_1 = models.CharField(max_length=34, blank=True, null=True)
    street_2 = models.CharField(max_length=34, blank=True, null=True)
    city = models.CharField(max_length=30, blank=True, null=True)
    state = models.CharField(max_length=2, blank=True, null=True)
    zip_code = models.CharField(max_length=9, blank=True, null=True)
    cmte_email_1 = models.CharField(max_length=100, blank=True, null=True)
    cmte_email_2 = models.CharField(max_length=100, blank=True, null=True)
    phone_number = models.CharField(max_length=30, blank=True, null=True)
    cmte_type = models.CharField(max_length=1, blank=True, null=True)
    cmte_dsgn = models.CharField(max_length=1, blank=True, null=True)
    cmte_filing_freq = models.CharField(max_length=1, blank=True, null=True)
    cmte_filed_type = models.CharField(max_length=1, blank=True, null=True)
    treasurer_last_name = models.CharField(max_length=90, blank=True, null=True)
    treasurer_first_name = models.CharField(max_length=90, blank=True, null=True)
    treasurer_middle_name = models.CharField(max_length=90, blank=True, null=True)
    treasurer_prefix = models.CharField(max_length=10, blank=True, null=True)
    treasurer_suffix = models.CharField(max_length=10, blank=True, null=True)
    last_update_date = models.TimeField()

    class Meta:
        managed = False
        db_table = "committee_lookup"


class My_Forms_View(models.Model):  # noqa N801
    cmte_id = models.CharField(primary_key=True, max_length=9)
    category = models.CharField(max_length=25)
    form_type = models.CharField(max_length=10)
    due_date = models.DateField(blank=True, null=True)
    form_description = models.CharField(max_length=300, blank=True, null=True)
    form_info = models.CharField(max_length=1000, blank=True, null=True)


class RefCmteTypeVsForms(models.Model):
    cmte_type = models.CharField(primary_key=True, max_length=1)
    cmte_dsgn = models.CharField(max_length=1)
    form_type = models.CharField(max_length=10)
    category = models.CharField(max_length=25)
    last_update_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "ref_cmte_type_vs_forms"
        unique_together = (("cmte_type", "cmte_dsgn", "form_type"),)


class RefFormTypes(models.Model):
    form_type = models.CharField(primary_key=True, max_length=10)
    form_description = models.CharField(max_length=300, blank=True, null=True)
    form_tooltip = models.CharField(max_length=1000, blank=True, null=True)
    form_pdf_url = models.CharField(max_length=500, blank=True, null=True)

    class Meta:
        managed = False
        db_table = "ref_form_types"


class RefFormsVsReports(models.Model):
    form_type = models.CharField(primary_key=True, max_length=10)
    report_type = models.CharField(max_length=10)
    filing_freq = models.CharField(max_length=1, blank=True, null=True)
    last_update_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "ref_forms_vs_reports"
        unique_together = (("form_type", "report_type"),)


class RefRptTypes(models.Model):
    rpt_type = models.CharField(primary_key=True, max_length=9)
    rpt_type_desc = models.CharField(max_length=200, blank=True, null=True)
    rpt_type_order = models.IntegerField(blank=True, null=True)
    last_update_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "ref_rpt_types"
