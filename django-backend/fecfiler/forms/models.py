
# Create your models here.
from django.db import models
from django.core.validators import FileExtensionValidator
from .validators import validate_is_pdf
from django.utils.translation import ugettext_lazy as _

#Table to store F99 attachment data (Refer this documentation: https://django-db-file-storage.readthedocs.io/en/master/)
class F99Attachment(models.Model):
    bytes = models.TextField()
    filename = models.CharField(max_length=255)
    mimetype = models.CharField(max_length=50)

class CommitteeInfo(models.Model):
    # Committee Information Table Model
    id = models.AutoField(primary_key=True)
    committeeid = models.CharField(max_length=9)
    committeename = models.CharField(max_length=200, null=False)
    street1 = models.CharField(max_length=34, null=False)
    street2 = models.CharField(max_length=34, null=True)
    text = models.TextField(max_length=20000, null=False, default="-")
    reason = models.CharField(max_length=3, null=False, default="-")
    city = models.CharField(max_length=30, null=False)
    state = models.CharField(max_length=2, null=False)
    zipcode = models.TextField(null=False, max_length=5)
    #zipcode = models.IntegerField(null=False)
    treasurerlastname = models.CharField(max_length=30, null=False)
    treasurerfirstname = models.CharField(max_length=20, null=False)
    treasurermiddlename = models.CharField(max_length=20, null=True)
    treasurerprefix = models.CharField(max_length=10, null=True)
    treasurersuffix = models.CharField(max_length=10, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True)
    isdeleted = models.BooleanField(default=False)
    is_submitted = models.BooleanField(default=False)
    signee = models.CharField(max_length=30, null= False, default = "-")
    email_on_file = models.TextField(max_length=100, null= False, default = "-")
    additional_email_1 = models.TextField(max_length=100, null= True, default = "-")
    additional_email_2 = models.TextField(max_length=100, null= True, default = "-")
    file = models.FileField(upload_to='forms.F99Attachment/bytes/filename/mimetype', null=True, blank=True, validators=[validate_is_pdf,])
    # implememted file upload using the following module: https://django-db-file-storage.readthedocs.io/en/master/
    form_type = models.CharField(max_length=3, default="F99")
    coverage_start_date = models.DateField(null=True)
    coverage_end_date = models.DateField(null=True)
    
    # class constructor
    def __unicode__(self):
        return self.committeename
    

    class Meta():
        verbose_name = _('CommitteeInfo')
        verbose_name_plural = _('CommitteeInfo')



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
    email_on_file = models.TextField(max_length=100, null= False, default = "-")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True)
    isdeleted = models.BooleanField(default=False)


    # class constructor
    def __unicode__(self):
        return self.committeename
    

    class Meta():
        verbose_name = _('Committee')
        verbose_name_plural = _('Committee')


    
