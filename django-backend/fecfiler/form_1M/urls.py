from django.conf.urls import url
from . import views


urlpatterns = [
    url(r"^f1M/form1M$", views.form1M, name="form1M"),
    url(r"^f1M/get_details$", views.get_details, name="get_details"),
    url(
        r"^f1M/get_original_reg_date$",
        views.get_original_registration_date,
        name="get_original_reg_date",
    ),
    url(
        r"^f1M/get_cmte_met_req_date$",
        views.get_committee_met_req_date,
        name="get_cmte_met_req_date",
    ),
    url(
        r"^f1M/delete_cand_f1m$",
        views.delete_candidate_f1m,
        name="delete_candidate_f1m",
    ),
]
