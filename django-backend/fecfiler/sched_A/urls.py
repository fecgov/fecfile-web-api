from django.conf.urls import url
from . import views


urlpatterns = [

    url(r'^sa/schedA$', views.schedA, name='schedA'),
    url(r'^sa/contribution_aggregate$', views.contribution_aggregate, name='contribution_aggregate'),
    # This API was brought in from CORE APP as it used few sched_A functions which were conflicting usage
    url(
        r"^core/trash_restore_transactions$",
        views.trash_restore_transactions,
        name="trash_restore_transactions",
    ),
    url(r'^sa/get_report_id_from_date$',
    views.get_report_id_from_date, name='get_report_id_from_date'),
]
