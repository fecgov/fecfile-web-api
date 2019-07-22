from django.conf.urls import url
from . import views


urlpatterns = [
    url(r'^sc/schedC$', views.schedC, name='schedC'),
    url(r'^sc/schedC1$', views.schedC1, name='schedC1'),
    url(r'^sc/schedC2$', views.schedC2, name='schedC2'),
]
