# Generated by Django 4.2.10 on 2024-03-25 16:45

from django.db import migrations
from django.db.models import Q


def set_aggregation_group_to_none_for_ie_memos(apps, schema_editor):
    transaction_model = apps.get_model("transactions", "Transaction")

    for transaction in transaction_model.objects.filter(
        Q(transaction_type_identifier__in=[
            "INDEPENDENT_EXPENDITURE_CREDIT_CARD_PAYMENT_MEMO",
            "INDEPENDENT_EXPENDITURE_STAFF_REIMBURSEMENT_MEMO",
            "INDEPENDENT_EXPENDITURE_PAYMENT_TO_PAYROLL_MEMO"
        ])
    ):
        transaction.aggregation_group = None
        transaction.save()


def reverse_removing_aggregation_group_for_ie_memos(apps, schema_editor):
    transaction_model = apps.get_model("transactions", "Transaction")

    for transaction in transaction_model.objects.filter(
        Q(transaction_type_identifier__in=[
            "INDEPENDENT_EXPENDITURE_CREDIT_CARD_PAYMENT_MEMO",
            "INDEPENDENT_EXPENDITURE_STAFF_REIMBURSEMENT_MEMO",
            "INDEPENDENT_EXPENDITURE_PAYMENT_TO_PAYROLL_MEMO"
        ])
    ):
        transaction.aggregation_group = "INDEPENDENT_EXPENDITURE"
        transaction.save()


class Migration(migrations.Migration):

    dependencies = [
        ("transactions", "0005_schedulec_report_coverage_from_date_and_more"),
    ]

    operations = [
        migrations.RunPython(
            set_aggregation_group_to_none_for_ie_memos,
            reverse_removing_aggregation_group_for_ie_memos,
        ),
    ]
