from django.conf.urls import url
from . import views, jsonmain, jsonsqlgenerate


urlpatterns = [

    url(
        r"^core/queue_transaction_message$",
        views.queue_transaction_message,
        name="queue_transaction_message",
    ), url(
        r"^core/validate_import_transactions$",
        views.validate_import_transactions,
        name="validate_import_transactions",
    ),
    url(
        r"^core/generate_contact_details_from_csv$",
        views.generate_contact_details_from_csv,
        name="generate_contact_details_from_csv",
    ),
    url(
        r"^core/queue_transaction_message$",
        views.queue_transaction_message,
        name="queue_transaction_message",
    ), url(
        r"^core/validate_import_transactions$",
        views.validate_import_transactions,
        name="validate_import_transactions",
    ),
    url(
        r"^core/chk_csv_uploaded_in_db$",
        views.chk_csv_uploaded_in_db,
        name="chk_csv_uploaded_in_db",
    ),
    url(
        r"^core/save_csv_md5_to_db$",
        views.save_csv_md5_to_db,
        name="save_csv_md5_to_db",
    ),
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
    url(
        r"^core/get_transaction_types$",
        views.get_transaction_types,
        name="get_transaction_types",
    ),
    url(r"^core/get_report_types$", views.get_report_types, name="get_report_types"),
    url(
        r"^core/get_dynamic_forms_fields$",
        views.get_dynamic_forms_fields,
        name="get_dynamic_forms_fields",
    ),
    url(r"^core/create_json_file$", views.create_json_file, name="create_json_file"),
    url(r"^core/entities$", views.entities, name="entities"),
    url(r"^core/levin_accounts$", views.levin_accounts, name="levin_accounts"),
    url(
        r"^core/autolookup_search_contacts$",
        views.autolookup_search_contacts,
        name="autolookup_search_contacts",
    ),
    url(
        r"^core/autolookup_expand$",
        views.autolookup_expand,
        name="autolookup_expand",
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
    url(
        r"^core/print_query$",
        jsonsqlgenerate.print_query,
        name="print_query",
    ),
    url(r"^core/print_preview_pdf$", views.print_preview_pdf, name="print_preview_pdf"),
    url(r"^core/reports$", views.reports, name="reports"),
    url(r"^core/upcoming_reports$", views.upcoming_reports, name="upcoming_reports"),
    url(r"^core/recent_saved_reports$", views.recent_saved_reports, name="recent_saved_reports"),
    url(r"^core/recent_submitted_reports$", views.recent_submitted_reports, name="recent_submitted_reports"),
    url(r"^core/submit_report$", views.submit_report, name="submit_report"),
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
    url(
        r"^core/address_validation$",
        views.address_validation,
        name="address_validation",
    ),
    url(
        r"^core/check_duplicate_address$",
        views.check_duplicate_address,
        name="check_duplicate_address",
    ),
    url(
        r"^core/create_amended_reports$",
        views.create_amended_reports,
        name="create_amended_reports",
    ),
    url(
        r"^core/new_report_update_date$",
        views.new_report_update_date,
        name="new_report_update_date",
    ),
    url(r"^core/get_report_status$", views.get_report_status, name="get_report_status"),
    url(
        r"^core/get_sched_c_loan_dynamic_forms_fields$",
        views.get_sched_c_loan_dynamic_forms_fields,
        name="get_sched_c_loan_dynamic_forms_fields",
    ),
    url(
        r"^core/get_sched_c_loanPayment_dynamic_forms_fields$",
        views.get_sched_c_loanPayment_dynamic_forms_fields,
        name="get_sched_c_loanPayment_dynamic_forms_fields",
    ),
    url(
        r"^core/get_sched_c_endorser_dynamic_forms_fields$",
        views.get_sched_c_endorser_dynamic_forms_fields,
        name="get_sched_c_endorser_dynamic_forms_fields",
    ),
    url(
        r"^core/prepare_Schedl_summary_data$",
        views.prepare_Schedl_summary_data,
        name=" prepare_Schedl_summary_data",
    ),
    url(
        r"^core/get_coverage_dates$",
        views.get_coverage_dates,
        name="get_coverage_dates",
    ),
    url(
        r"^core/reports_memo_text$",
        views.reports_memo_text,
        name="reports_memo_text",
    ),
    url(
        r"^core/get_child_max_transaction_amount$",
        views.get_child_max_transaction_amount,
        name="get_child_max_transaction_amount",
    ),
    url(
        r"^core/report/additionalEmails$",
        views.save_additional_email,
        name="save_additional_email",
    ),
    url(
        r"^core/get_f24_reports$",
        views.get_f24_reports,
        name="get_f24_reports",
    ),
    url(
        r"^core/get_notifications_count$",
        views.get_notifications_count,
        name="get_notifications_count",
    ),
    url(
        r"^core/get_notifications_counts$",
        views.get_notifications_counts,
        name="get_notifications_counts",
    ),
    url(
        r"^core/get_notifications$",
        views.get_notifications,
        name="get_notifications",
    ),
    url(
        r"^core/get_notification$",
        views.get_notification,
        name="get_notification",
    ),
    url(
        r"^core/cashOnHand$",
        views.cashOnHand,
        name="cashOnHand",
    ),
    url(
        r"^core/cashOnHandInfoStatus$",
        views.cashOnHandInfoStatus,
        name="cashOnHandInfoStatus",
    ),
    url(
        r"^core/contactLogs$",
        views.contact_logs,
        name="contact_logs",
    ),
    url(
        r"^core/contactReportDetails$",
        views.contact_report_details,
        name="contact_report_details",
    ),
    url(
        r"^core/contact_notes$",
        views.contact_notes,
        name="contact_notes",
    ),
    url(
        r"^core/import_fecfile",
        views.import_fecfile,
        name="import_fecfile",
    ),
]
