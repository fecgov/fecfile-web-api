# Generated by Django 3.2.12 on 2022-09-09 16:41

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ("memo_text", "0003_report_id"),
        ("scha_transactions", "0018_report_id"),
        ("f3x_summaries", "0021_f3xsummary_submission_keys"),
    ]

    operations = [
        migrations.AlterField(
            model_name="f3xsummary",
            name="id",
            field=models.IntegerField(),
        ),
        migrations.AlterField(
            model_name="f3xsummary",
            name="uuid",
            field=models.UUIDField(
                default=uuid.uuid4,
                editable=False,
                primary_key=True,
                serialize=False,
                unique=True,
            ),
        ),
    ]
