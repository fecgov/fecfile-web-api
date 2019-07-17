from django.conf.urls import url
from . import views


urlpatterns = [
    url(r'^sa/schedC$', views.schedC, name='schedC'),
    url(r'^sa/schedC1$', views.schedC1, name='schedC1'),
    url(r'^sa/schedC2$', views.schedC2, name='schedC2'),
]
