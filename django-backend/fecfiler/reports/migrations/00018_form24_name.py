from django.db import migrations, models
from django_migration_linter import IgnoreMigration


def update_form24_names(apps, schema_editor):
    form24 = apps.get_model("reports", "Form24")
    form24_objects = list(form24.objects.all())
    for index, form in enumerate(form24_objects, start=1):
        report_type = form.report_type_24_48
        form.name = f"{report_type}-HOUR Report: {index}"
        form.save()


def reverse_update_form24_names(apps, schema_editor):
    form24 = apps.get_model("reports", "Form24")
    form24_objects = form24.objects.all()
    for form in form24_objects:
        form.name = None  # Or set it to some placeholder value if you prefer
        form.save()


class Migration(migrations.Migration):

    dependencies = [
        ("reports", "0017_form99_filing_frequency_form99_pdf_attachment"),
    ]

    operations = [
        IgnoreMigration(),
        migrations.AddField(
            model_name="form24",
            name="name",
            field=models.TextField(null=False, blank=False, unique=True),
        ),
        migrations.RunPython(update_form24_names, reverse_update_form24_names),
    ]
