from django.conf.urls import url
from . import views


urlpatterns = [
    url(r"^sh1/schedH1$", views.schedH1, name="schedH1"),
    url(r"^sh2/schedH2$", views.schedH2, name="schedH2"),
    url(
        r"^sh2/get_h2_summary_table$",
        views.get_h2_summary_table,
        name="get_h2_summary_table",
    ),
    url(
        r"^sh2/get_h2_type_events$", views.get_h2_type_events, name="get_h2_type_events"
    ),
    url(
        r"^sh3/get_h3_total_amount$",
        views.get_h3_total_amount,
        name="get_h3_total_amount",
    ),
    url(
        r"^sh3/get_h3_aggregate_amount$",
        views.get_h3_aggregate_amount,
        name="get_h3_aggregate_amount",
    ),
    url(r"^sh3/get_h3_summary$", views.get_h3_summary, name="get_h3_summary"),
    url(
        r"^sh3/get_h3_account_names$",
        views.get_h3_account_names,
        name="get_h3_account_names",
    ),
    url(r"^sh5/get_h5_summary$", views.get_h5_summary, name="get_h5_summary"),
    url(r"^sh3/schedH3$", views.schedH3, name="schedH3"),
    url(r"^sh4/schedH4$", views.schedH4, name="schedH4"),
    url(r"^sh5/schedH5$", views.schedH5, name="schedH5"),
    url(r"^sh6/schedH6$", views.schedH6, name="schedH6"),
    url(
        r"^sh3/get_sched_h3_breakdown$",
        views.get_sched_h3_breakdown,
        name="get_sched_h3_breakdown",
    ),
    url(
        r"^sh5/get_sched_h5_breakdown$",
        views.get_sched_h5_breakdown,
        name="get_sched_h5_breakdown",
    ),
    url(r"^sh1/get_h1_percentage$", views.get_h1_percentage, name="get_h1_percentage"),
    url(
        r"^sh1/get_fed_nonfed_share$",
        views.get_fed_nonfed_share,
        name="get_fed_nonfed_share",
    ),
    url(
        r"^sh1/validate_h1_h2_exist$",
        views.validate_h1_h2_exist,
        name="validate_h1_h2_exist",
    ),
    url(r"^sh1/validate_pac_h1$", views.validate_pac_h1, name="validate_pac_h1"),
]
