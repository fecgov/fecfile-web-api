from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("f3x_summaries", "0022_remove_id"),
    ]

    operations = [
        migrations.AlterField(
            model_name="f3xsummary",
            name="committee_account",
            field=models.IntegerField(),
        ),
    ]
