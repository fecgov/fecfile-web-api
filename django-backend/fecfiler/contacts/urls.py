from django.conf.urls import url
from . import views

urlpatterns = [
    url(r"^contact/upload$", views.upload_contact, name="importContactFile"),
    url(r"^contact/delete$", views.delete_contact, name="deleteContact"),
]