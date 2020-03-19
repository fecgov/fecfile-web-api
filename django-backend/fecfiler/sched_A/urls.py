from django.conf.urls import url
from . import views


urlpatterns = [
    url(r"^sa/schedA$", views.schedA, name="schedA"),
    url(
        r"^sa/contribution_aggregate$",
        views.contribution_aggregate,
        name="contribution_aggregate",
    ),
    url(
        r"^sa/force_aggregate_sa$", views.force_aggregate_sa, name="force_aggregate_sa"
    ),
    url(
        r"^sa/force_unaggregate_sa$",
        views.force_unaggregate_sa,
        name="force_unaggregate_sa",
    ),
    url(
        r"^sa/force_itemize_sa$", views.force_itemize_sa, name="force_itemize_sa"
    ),
    url(
        r"^sa/force_unitemize_sa$",
        views.force_unitemize_sa,
        name="force_unitemize_sa",
    ),
    # This API was brought in from CORE APP as it used few sched_A functions which were conflicting usage
    url(
        r"^core/trash_restore_transactions$",
        views.trash_restore_transactions,
        name="trash_restore_transactions",
    ),
    url(
        r"^sa/get_report_id_from_date$",
        views.get_report_id_from_date,
        name="get_report_id_from_date",
    ),
]
