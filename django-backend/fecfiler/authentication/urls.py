from django.conf.urls import url
from . import views, login

urlpatterns = [
    url(r"^user/manage$", views.manage_user, name="manageuser"),
    url(r"^user/manage/toggle$", views.toggle_user, name="status"),
    url(r"^user/info$", views.current_user, name="userInfo"),
    url(r"^user/login/authenticate$", login.authenticate_login, name="login_authenticate"),
    url(r"^user/login/verify$", login.verify_login, name="code-verify-login")
]