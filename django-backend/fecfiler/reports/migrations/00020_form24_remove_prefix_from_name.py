from django.db import migrations
import re


def remove_prefix_from_form24_names(apps, schema_editor):
    form24 = apps.get_model("reports", "Form24")
    form24_objects = list(form24.objects.all())
    for form in form24_objects:
        split_name = re.split(r"^24-Hour:|^48-Hour:", form.name, flags=re.IGNORECASE)
        if len(split_name) > 1:
            form.name = split_name[1].strip()
            form.save()


class Migration(migrations.Migration):

    dependencies = [
        ("reports", "00019_form24_name_fix"),
    ]

    operations = [
        migrations.RunPython(remove_prefix_from_form24_names, migrations.RunPython.noop),
    ]
