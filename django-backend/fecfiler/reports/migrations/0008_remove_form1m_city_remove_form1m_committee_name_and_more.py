# Generated by Django 4.2.10 on 2024-04-19 19:10

from django.db import migrations, models
import structlog

logger = structlog.get_logger(__name__)


def migrate_committee_data(apps, schema_editor):
    Report = apps.get_model("reports", "Report")  # noqa
    Form24 = apps.get_model("reports", "Form24")  # noqa
    Form3x = apps.get_model("reports", "Form3X")  # noqa
    Form99 = apps.get_model("reports", "Form99")  # noqa
    Form1m = apps.get_model("reports", "Form1M")  # noqa

    for form in Form24.objects.all():
        report = Report.objects.filter(form_24=form).first()
        if report is not None:
            report.street_1 = form.street_1
            report.street_2 = form.street_2
            report.city = form.city
            report.state = form.state
            report.zip = form.zip
            report.save()
        else:
            logger.error(f"F24 Form has no corresponding report! {form}")

    for form in Form3x.objects.all():
        report = Report.objects.filter(form_3x=form).first()
        if report is not None:
            report.street_1 = form.street_1
            report.street_2 = form.street_2
            report.city = form.city
            report.state = form.state
            report.zip = form.zip
            report.save()
        else:
            logger.error(f"F3X Form has no corresponding report! {form}")

    for form in Form99.objects.all():
        report = Report.objects.filter(form_99=form).first()
        if report is not None:
            report.committee_name = form.committee_name
            report.street_1 = form.street_1
            report.street_2 = form.street_2
            report.city = form.city
            report.state = form.state
            report.zip = form.zip
            report.save()
        else:
            logger.error(f"F99 Form has no corresponding report! {form}")

    for form in Form1m.objects.all():
        report = Report.objects.filter(form_1m=form).first()
        if report is not None:
            report.committee_name = form.committee_name
            report.street_1 = form.street_1
            report.street_2 = form.street_2
            report.city = form.city
            report.state = form.state
            report.zip = form.zip
            report.save()
        else:
            logger.error(f"F1M Form has no corresponding report! {form}")


class Migration(migrations.Migration):

    dependencies = [
        ("reports", "0007_remove_report_deleted"),
    ]

    operations = [
        migrations.AddField(
            model_name="report",
            name="city",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="report",
            name="committee_name",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="report",
            name="state",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="report",
            name="street_1",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="report",
            name="street_2",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="report",
            name="zip",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.RunPython(migrate_committee_data),
        migrations.RemoveField(
            model_name="form1m",
            name="city",
        ),
        migrations.RemoveField(
            model_name="form1m",
            name="committee_name",
        ),
        migrations.RemoveField(
            model_name="form1m",
            name="state",
        ),
        migrations.RemoveField(
            model_name="form1m",
            name="street_1",
        ),
        migrations.RemoveField(
            model_name="form1m",
            name="street_2",
        ),
        migrations.RemoveField(
            model_name="form1m",
            name="zip",
        ),
        migrations.RemoveField(
            model_name="form24",
            name="city",
        ),
        migrations.RemoveField(
            model_name="form24",
            name="state",
        ),
        migrations.RemoveField(
            model_name="form24",
            name="street_1",
        ),
        migrations.RemoveField(
            model_name="form24",
            name="street_2",
        ),
        migrations.RemoveField(
            model_name="form24",
            name="zip",
        ),
        migrations.RemoveField(
            model_name="form3x",
            name="city",
        ),
        migrations.RemoveField(
            model_name="form3x",
            name="state",
        ),
        migrations.RemoveField(
            model_name="form3x",
            name="street_1",
        ),
        migrations.RemoveField(
            model_name="form3x",
            name="street_2",
        ),
        migrations.RemoveField(
            model_name="form3x",
            name="zip",
        ),
        migrations.RemoveField(
            model_name="form99",
            name="city",
        ),
        migrations.RemoveField(
            model_name="form99",
            name="committee_name",
        ),
        migrations.RemoveField(
            model_name="form99",
            name="state",
        ),
        migrations.RemoveField(
            model_name="form99",
            name="street_1",
        ),
        migrations.RemoveField(
            model_name="form99",
            name="street_2",
        ),
        migrations.RemoveField(
            model_name="form99",
            name="zip",
        ),
    ]
