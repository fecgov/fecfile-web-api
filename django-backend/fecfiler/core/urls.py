from  django.conf.urls import url
from . import views


urlpatterns = [
    url(r'^core/get_filed_report_types$', views.get_filed_report_types, name='get_filed_report_types'),
    url(r'^core/get_filed_form_types$', views.get_filed_form_types, name='get_filed_form_types'),
    url(r'^core/get_transaction_categories$', views.get_transaction_categories, name='get_transaction_categories'),
    url(r'^core/get_report_types$', views.get_report_types, name='get_report_types'),
    url(r'^core/get_dynamic_forms_fields$', views.get_dynamic_forms_fields, name='get_dynamic_forms_fields'),
    url(r'^core/create_json_file$', views.create_json_file, name='create_json_file'),
    url(r'^core/create_f3x_expenditure_json_file$', views.create_f3x_expenditure_json_file, name='create_f3x_expenditure_json_file'),
    url(r'^core/reports$', views.reports, name='reports'),
    url(r'^core/entities$', views.entities, name='entities'),
    url(r'^core/search_entities$', views.search_entities, name='search_entities'),
    url(r'^core/get_all_transactions$', views.get_all_transactions, name='get_all_transactions'),
    url(r'^core/state$', views.state, name='state'),
    url(r'^core/get_all_deleted_transactions$', views.get_all_deleted_transactions, name='get_all_deleted_transactions'),
    url(r'^core/summary_table$', views.summary_table, name='summary_table'),
     url(r'^core/get_FormTypes$', views.get_FormTypes, name='get_FormTypes'),
    url(r'^core/get_ReportTypes$', views.get_ReportTypes, name='get_ReportTypes'),
    url(r'^core/get_AmendmentIndicators$', views.get_AmendmentIndicators, name='get_AmendmentIndicators'),
    url(r'^core/get_Statuss$', views.get_Statuss, name='get_Statuss'),
    url(r'^core/build_form3x_json_file$', views.build_form3x_json_file, name='build_form3x_json_file'),
    # url(r'^core/create_f3x_partner_json_file$', views.create_f3x_partner_json_file, name='create_f3x_partner_json_file'),
    # url(r'^core/create_f3x_json_file$', views.create_f3x_json_file, name='create_f3x_json_file'),
]
