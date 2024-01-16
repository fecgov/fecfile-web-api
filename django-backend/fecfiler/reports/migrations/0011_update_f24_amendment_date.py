from django.db import migrations


def update_f24_original_amendment_date(apps, schema_editor):
    Report = apps.get_model("reports", "Report")  # noqa
    reports_to_update = Report.objects.filter(
        form_type="F24A",
        form_24__isnull=False,
        upload_submission__isnull=False
    )
    for report in reports_to_update:
        report.form_24.original_amendment_date = report.upload_submission.created
        report.form_24.save()


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("reports", "0010_form1m_committee_name_form1m_contact_affiliated_and_more"),
    ]

    operations = [
        migrations.RunPython(
            update_f24_original_amendment_date,
            migrations.RunPython.noop
        ),
    ]
