from  django.conf.urls import url
from . import views


urlpatterns = [

    url(r'^sb/schedB$', views.schedB, name='schedB'),
]