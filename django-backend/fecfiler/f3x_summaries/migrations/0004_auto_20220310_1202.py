# Generated by Django 3.2.12 on 2022-03-10 17:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("f3x_summaries", "0003_auto_20220303_1326"),
    ]

    operations = [
        migrations.AlterField(
            model_name="f3xsummary",
            name="date_signed",
            field=models.TextField(null=True),
        ),
        migrations.AlterField(
            model_name="f3xsummary",
            name="filer_committee_id_number",
            field=models.TextField(null=True),
        ),
        migrations.AlterField(
            model_name="f3xsummary",
            name="form_type",
            field=models.CharField(
                choices=[("F3XT", "F3XT"), ("F3XN", "F3XN"), ("F3XA", "F3XA")],
                default="F3XN",
                max_length=255,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="f3xsummary",
            name="treasurer_first_name",
            field=models.TextField(null=True),
        ),
        migrations.AlterField(
            model_name="f3xsummary",
            name="treasurer_last_name",
            field=models.TextField(null=True),
        ),
    ]
