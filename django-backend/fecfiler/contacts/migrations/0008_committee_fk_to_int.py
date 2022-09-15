from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("contacts", "0007_contact_uuid"),
    ]

    operations = [
        migrations.AlterField(
            model_name="contact",
            name="committee_account",
            field=models.IntegerField(),
        ),
    ]
