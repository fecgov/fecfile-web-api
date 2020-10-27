from django.conf.urls import url
#from . import views, duplicate, merge, export
from .views import views
from .views import duplicate
from .views import merge
from .views import export

urlpatterns = [
    url(r"^contact/upload$", views.upload_contact, name="importContactFile"),
    url(r"^contact/delete$", views.delete_contact, name="deleteContact"),
    url(r"^contact/details$", export.contact_details, name="contactDetail"),
    url(r"^contact/validation$", duplicate.validate_contact, name="validateContactFile"),
    url(r"^contact/ignore/merge$", duplicate.ignore_merge, name="ignoreMerge"),
    url(r"^contact/cancel/import$", duplicate.cancel_import, name="cancelImport"),
    url(r"^contact/duplicate$", duplicate.get_duplicate_contact, name="duplicateContact"),
    url(r"^contact/merge/options$", merge.merge_option, name="mergeOption"),
    url(r"^contact/merge/save$", merge.merge_contact, name="mergeContact"),
    url(r"^contact/template$", views.download_template, name="downloadTemplate"),
]

