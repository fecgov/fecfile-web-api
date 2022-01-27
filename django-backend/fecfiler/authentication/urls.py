from django.conf.urls import url
from . import views, login, register

urlpatterns = [
    url(r"^user/manage$", views.manage_user, name="manageuser"),
    url(r"^user/manage/toggle$", views.toggle_user, name="status"),
    url(r"^user/info$", views.current_user, name="userInfo"),
    url(r"^user/login/authenticate$", login.authenticate_login, name="login_authenticate"),
    url(r"^user/login/verify$", login.verify_login, name="code-verify-login"),
    url(r"^user/register/authenticate$", register.authenticate, name="register_authenticate"),
    url(r"^user/register/verify$", register.code_verify_register, name="register-verify"),
    url(r"^user/register/password$", register.create_password, name="register-password"),
    url(r"^user/register/getAnotherPersonalKey$", register.get_another_personal_key, name="get_another_personal_key"),
    url(r"^user/register/get_committee_details$", register.get_committee_details, name="get_committee_details"),

]
