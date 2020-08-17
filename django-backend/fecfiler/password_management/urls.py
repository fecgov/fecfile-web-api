from django.conf.urls import url
from . import views

urlpatterns = [
    url(r"^password/authenticate$", views.authenticate_password, name="authenticate-password"),
    url(r"^password/reset/options$", views.reset_options_password, name="authentication-options"),
    url(r"^password/code/verify$", views.code_verify_password, name="code-verify"),
    url(r"^password/reset$", views.reset_password, name="reset-password"),
]
