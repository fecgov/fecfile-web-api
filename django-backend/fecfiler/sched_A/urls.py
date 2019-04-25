from  django.conf.urls import url
from . import views


urlpatterns = [

    url(r'^sa/schedA$', views.schedA, name='schedA'),
    url(r'^sa/aggregate_amount$', views.aggregate_amount, name='aggregate_amount'),
]