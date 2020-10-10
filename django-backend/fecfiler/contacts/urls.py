from django.conf.urls import url
from . import views, export

urlpatterns = [
    url(r"^contact/upload$", views.upload_contact, name="importContactFile"),
    url(r"^contact/delete$", views.delete_contact, name="deleteContact"),
    url(r"^contact/details$", export.contact_details, name="contactDetail"),
]