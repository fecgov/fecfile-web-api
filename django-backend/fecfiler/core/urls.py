from django.conf.urls import url
from . import views, jsonmain


urlpatterns = [
    url(r'^core/get_filed_report_types$',
        views.get_filed_report_types, name='get_filed_report_types'),
    url(r'^core/get_filed_form_types$',
        views.get_filed_form_types, name='get_filed_form_types'),
    url(r'^core/get_transaction_categories$',
        views.get_transaction_categories, name='get_transaction_categories'),
    url(r'^core/get_report_types$', views.get_report_types, name='get_report_types'),
    url(r'^core/get_dynamic_forms_fields$',
        views.get_dynamic_forms_fields, name='get_dynamic_forms_fields'),
    url(r'^core/create_json_file$', views.create_json_file, name='create_json_file'),
    url(r'^core/entities$', views.entities, name='entities'),
    url(r'^core/autolookup_search_contacts$', views.autolookup_search_contacts, name='autolookup_search_contacts'),
    url(r'^core/get_all_transactions$',
        views.get_all_transactions, name='get_all_transactions'),
    url(r'^core/state$', views.state, name='state'),
    url(r'^core/get_all_trashed_transactions$',
        views.get_all_trashed_transactions, name='get_all_trashed_transactions'),
    url(r'^core/trash_restore_transactions$',
        views.trash_restore_transactions, name='trash_restore_transactions'),
    url(r'^core/get_summary_table$', views.get_summary_table, name='get_summary_table'),
    url(r'^core/thirdNavTransactionTypes$', views.get_thirdNavigationTransactionTypes,
        name='get_thirdNavigationTransactionTypes'),
    url(r'^core/get_FormTypes$', views.get_FormTypes, name='get_FormTypes'),
    url(r'^core/get_ReportTypes$', views.get_ReportTypes, name='get_ReportTypes'),
    url(r'^core/get_AmendmentIndicators$',
        views.get_AmendmentIndicators, name='get_AmendmentIndicators'),
    url(r'^core/get_Statuss$', views.get_Statuss, name='get_Statuss'),
    url(r'^core/get_ItemizationIndicators$',
        views.get_ItemizationIndicators, name='get_ItemizationIndicators'),
    url(r'^core/get_report_info$', views.get_report_info, name='get_report_info'),
    url(r'^core/create_json_builders$', jsonmain.create_json_builders, name='create_json_builders'),
    url(r'^core/print_preview_pdf$', views.print_preview_pdf, name='print_preview_pdf'),
    url(r'^core/reports$', views.reports, name='reports'),


]
