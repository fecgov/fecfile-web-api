from django.conf.urls import url
from . import views

urlpatterns = [
    url(r"^contact/upload$", views.upload_contact, name="importContactFile"),
]