from django.conf.urls import url
from . import views, jsonmain, jsonsqlgenerate


urlpatterns = [
    url(
        r"^core/get_filed_report_types$",
        views.get_filed_report_types,
        name="get_filed_report_types",
    ),
    url(
        r"^core/get_filed_form_types$",
        views.get_filed_form_types,
        name="get_filed_form_types",
    ),
    url(
        r"^core/get_transaction_categories$",
        views.get_transaction_categories,
        name="get_transaction_categories",
    ),
    url(r"^core/get_report_types$", views.get_report_types, name="get_report_types"),
    url(
        r"^core/get_dynamic_forms_fields$",
        views.get_dynamic_forms_fields,
        name="get_dynamic_forms_fields",
    ),
    url(r"^core/create_json_file$", views.create_json_file, name="create_json_file"),
    url(r"^core/entities$", views.entities, name="entities"),
    url(
        r"^core/autolookup_search_contacts$",
        views.autolookup_search_contacts,
        name="autolookup_search_contacts",
    ),
    url(
        r"^core/get_all_transactions$",
        views.get_all_transactions,
        name="get_all_transactions",
    ),
    url(r"^core/state$", views.state, name="state"),
    url(
        r"^core/get_all_trashed_transactions$",
        views.get_all_trashed_transactions,
        name="get_all_trashed_transactions",
    ),
    # Moved this API to Sched_A APP as there were few functions restricting its use
    # url(
    #     r"^core/trash_restore_transactions$",
    #     views.trash_restore_transactions,
    #     name="trash_restore_transactions",
    # ),
    url(r"^core/get_summary_table$", views.get_summary_table, name="get_summary_table"),
    url(
        r"^core/thirdNavTransactionTypes$",
        views.get_thirdNavigationTransactionTypes,
        name="get_thirdNavigationTransactionTypes",
    ),
    url(r"^core/get_FormTypes$", views.get_FormTypes, name="get_FormTypes"),
    url(r"^core/get_ReportTypes$", views.get_ReportTypes, name="get_ReportTypes"),
    url(
        r"^core/get_AmendmentIndicators$",
        views.get_AmendmentIndicators,
        name="get_AmendmentIndicators",
    ),
    url(r"^core/get_Statuss$", views.get_Statuss, name="get_Statuss"),
    url(
        r"^core/get_ItemizationIndicators$",
        views.get_ItemizationIndicators,
        name="get_ItemizationIndicators",
    ),
    url(r"^core/get_report_info$", views.get_report_info, name="get_report_info"),
    url(
        r"^core/create_json_builders$",
        jsonmain.create_json_builders,
        name="create_json_builders",
    ),
    url(
        r"^core/sample_sql_generate$",
        jsonsqlgenerate.sample_sql_generate,
        name="sample_sql_generate",
    ),
    url(r"^core/print_preview_pdf$", views.print_preview_pdf, name="print_preview_pdf"),
    url(r"^core/reports$", views.reports, name="reports"),
    url(r"^core/contacts$", views.contacts, name="contacts"),
    url(
        r"^core/delete_trashed_transactions$",
        views.delete_trashed_transactions,
        name="delete_trashed_transactions",
    ),
    url(
        r"^core/get_loan_debt_summary$",
        views.get_loan_debt_summary,
        name="get_loan_debt_summary",
    ),
    url(
        r"^core/prepare_json_builders_data$",
        views.prepare_json_builders_data,
        name="prepare_json_builders_data",
    ),
    url(
        r"^core/get_contacts_dynamic_forms_fields$",
        views.get_contacts_dynamic_forms_fields,
        name="get_contacts_dynamic_forms_fields",
    ),
    url(r"^core/get_entityTypes$", views.get_entityTypes, name="get_entityTypes"),
    url(r"^core/contactsTable$", views.contactsTable, name="contactsTable"),
    url(
        r"^core/get_all_trashed_reports$",
        views.get_all_trashed_reports,
        name="get_all_trashed_reports",
    ),
    url(
        r"^core/delete_trashed_reports$",
        views.delete_trashed_reports,
        name="delete_trashed_reports",
    ),
    url(
        r"^core/trash_restore_report$",
        views.trash_restore_report,
        name="trash_restore_report",
    ),
    url(
        r"^core/get_all_trashed_contacts$",
        views.get_all_trashed_contacts,
        name="get_all_trashed_contacts",
    ),
    url(
        r"^core/delete_trashed_contacts$",
        views.delete_trashed_contacts,
        name="delete_trashed_contacts",
    ),
    url(
        r"^core/trash_restore_contact$",
        views.trash_restore_contact,
        name="trash_restore_contact",
    ),
    url(
        r"^core/clone_a_transaction$",
        views.clone_a_transaction,
        name="clone_a_transaction",
    ),
    # url(r"^core/get_filler_transaction_type$", views.get_filler_transaction_type, name="get_filler_transaction_type"),
]
