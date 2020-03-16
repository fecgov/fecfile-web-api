from  django.conf.urls import url
from . import views


urlpatterns = [

    url(r'^sb/schedB$', views.schedB, name='schedB'),
    url(
        r"^sb/force_itemize_sb$", views.force_itemize_sb, name="force_itemize_sb"
    ),
    url(
        r"^sb/force_unitemize_sb$",
        views.force_unitemize_sb,
        name="force_unitemize_sb",
    ),
    url(
        r"^sb/force_aggregate_sb$", views.force_aggregate_sb, name="force_aggregate_sb"
    ),
    url(
        r"^sb/force_unaggregate_sb$",
        views.force_unaggregate_sb,
        name="force_unaggregate_sb",
    ),
]