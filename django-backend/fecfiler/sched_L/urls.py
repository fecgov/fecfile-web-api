from django.conf.urls import url
from . import views


urlpatterns = [
    url(r"^sl/schedL$", views.schedL, name="schedL"),
    url(
        r"^sl/get_sl_summary_table$",
        views.get_sl_summary_table,
        name="get_sl_summary_table",
    ),
]
