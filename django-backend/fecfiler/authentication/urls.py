from django.conf.urls import url
from . import views

urlpatterns = [
    url(r"^user/manage$", views.manage_user, name="manageuser")
]