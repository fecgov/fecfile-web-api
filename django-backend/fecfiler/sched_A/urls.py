from  django.conf.urls import url
from . import views


urlpatterns = [

    url(r'^sa/schedA$', views.schedA, name='schedA'),
]