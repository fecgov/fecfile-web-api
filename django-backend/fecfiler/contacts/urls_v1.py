from django.conf.urls import url
from . import contacts_committee
from .views_v1 import views
from .views_v1 import duplicate
from .views_v1 import merge
from .views_v1 import export

urlpatterns = [
    url(r"^contact/upload$", views.upload_contact, name="importContactFile"),
    url(r"^contact/delete$", views.delete_contact, name="deleteContact"),
    url(r"^contact/details$", export.contact_details, name="contactDetail"),
    url(
        r"^contact/validation$", duplicate.validate_contact, name="validateContactFile"
    ),
    url(r"^contact/ignore/merge$", duplicate.ignore_merge, name="ignoreMerge"),
    url(r"^contact/cancel/import$", duplicate.cancel_import, name="cancelImport"),
    url(
        r"^contact/duplicate$", duplicate.get_duplicate_contact, name="duplicateContact"
    ),
    url(r"^contact/merge/options$", merge.merge_option, name="mergeOption"),
    url(r"^contact/merge/save$", merge.merge_contact, name="mergeContact"),
    url(r"^contact/template$", views.download_template, name="downloadTemplate"),
    url(
        r"^contact/transaction/upload$",
        contacts_committee.upload_cand_contact,
        name="OtherContact",
    ),
    url(
        r"^contact/transaction/ignore/merge$",
        duplicate.ignore_merge,
        name="ignoreMerge",
    ),
    url(
        r"^contact/transaction/cancel/import$",
        duplicate.cancel_import,
        name="cancelImport",
    ),
    url(
        r"^contact/transaction/duplicate$",
        duplicate.get_duplicate_contact,
        name="duplicateContact",
    ),
    url(r"^contact/transaction/merge/options$", merge.merge_option, name="mergeOption"),
    url(r"^contact/transaction/merge/save$", merge.merge_contact, name="mergeContact"),
]
