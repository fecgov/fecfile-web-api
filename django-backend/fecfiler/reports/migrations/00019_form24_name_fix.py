from django.db import migrations


def update_form24_names(apps, schema_editor):
    form24 = apps.get_model("reports", "Form24")
    form24_objects = list(form24.objects.all())
    for form in form24_objects:
        report_type = form.report_type_24_48
        form.name = f"{report_type}-HOUR: Report of Independent Expenditure"
        form.save()


class Migration(migrations.Migration):

    dependencies = [
        ("reports", "00018_form24_name"),
    ]

    operations = [
        migrations.RunPython(update_form24_names, migrations.RunPython.noop),
    ]
