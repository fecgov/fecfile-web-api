from django.conf.urls import url
from . import views


urlpatterns = [

    url(r'^se/schedE$', views.schedE, name='schedE'),
    url(
        r"^se/get_sched_e_ytd_amount$",
        views.get_sched_e_ytd_amount,
        name="get_sched_e_ytd_amount",
    ),
    url(
        r"^se/force_aggregate_se$", views.force_aggregate_se, name="force_aggregate_se"
    ),
    url(
        r"^se/force_unaggregate_se$",
        views.force_unaggregate_se,
        name="force_unaggregate_se",
    ),
    url(
        r"^se/mirror_to_F24$",
        views.mirror_to_F24,
        name="mirror_to_F24",
    ),
]
