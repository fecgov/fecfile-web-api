# Generated by Django 3.2.12 on 2022-09-12 20:34

from django.db import migrations, models


def update_uuid(apps, schema_editor):
    F3XSummary = apps.get_model("f3x_summaries", "F3XSummary")  # noqa
    SchATransaction = apps.get_model("scha_transactions", "SchATransaction")  # noqa
    report_uuid = F3XSummary.objects.filter(
        id=models.OuterRef("report_old")
    ).values_list("uuid")[:1]
    SchATransaction.objects.update(report=models.Subquery(report_uuid))


class Migration(migrations.Migration):

    dependencies = [
        ("scha_transactions", "0019_report_id"),
        ("f3x_summaries", "0021_f3xsummary_uuid_primary"),
    ]

    operations = [
        migrations.RenameField(
            model_name="schatransaction",
            old_name="report",
            new_name="report_old",
        ),
        migrations.AddField(
            model_name="schatransaction",
            name="report",
            field=models.ForeignKey(
                null=True,
                on_delete=models.deletion.CASCADE,
                to="f3x_summaries.F3XSummary",
            ),
        ),
        migrations.RunPython(update_uuid),
        migrations.RemoveField(
            model_name="schatransaction",
            name="report_old",
        ),
    ]
