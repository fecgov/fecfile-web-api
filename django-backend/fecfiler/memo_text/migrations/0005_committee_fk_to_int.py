from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("memo_text", "0004_report_fk"),
    ]

    operations = [
        migrations.AlterField(
            model_name="memotext",
            name="committee_account",
            field=models.IntegerField(),
        ),
    ]
