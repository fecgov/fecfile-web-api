from django.conf.urls import url
from . import views


urlpatterns = [

    url(r'^se/schedE$', views.schedE, name='schedE'),
    url(
        r"^se/get_sched_e_ytd_amount$",
        views.get_sched_e_ytd_amount,
        name="get_sched_e_ytd_amount",
    ),
    
]
