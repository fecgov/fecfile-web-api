from django.conf.urls import url
from . import views

# url's for comm_info and get_default_reasons for filing

urlpatterns = [
    url(r"^f99/create_f99_info$", views.create_f99_info, name="create_f99_info"),
    url(r"^f99/update_f99_info$", views.update_f99_info, name="update_f99_info"),
    url(r"^f99/get_default_reasons$", views.get_f99_reasons, name="get_f99_reasons"),
    url(r"^f99/submit_comm_info$", views.submit_comm_info, name="submit_comm_info"),
    url(r"^f99/validate_f99$", views.validate_f99, name="validate_f99"),
    url(r"^core/create_committee$", views.create_committee, name="create_committee"),
    url(r"^f99/save_print_f99$", views.save_print_f99, name="save_print_f99"),
    url(r"^f99/update_print_f99$", views.update_print_f99, name="update_print_f99"),
    url(r"^f99/print_pdf$", views.print_pdf, name="print_pdf"),
    url(r"^f99/submit_formf99$", views.submit_formf99, name="submit_formf99"),
]
