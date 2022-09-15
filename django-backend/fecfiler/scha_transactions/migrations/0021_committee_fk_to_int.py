from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("scha_transactions", "0020_report_fk"),
    ]

    operations = [
        migrations.AlterField(
            model_name="schatransaction",
            name="committee_account",
            field=models.IntegerField(),
        ),
    ]
