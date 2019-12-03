from django.conf.urls import url
from . import views


urlpatterns = [

    url(r'^sf/schedF$', views.schedF, name='schedF'),
    url(r'^sf/get_aggregate$', views.get_aggregate_general_elec_exp, name='get_aggregate_general_elec_exp'),
    
]
