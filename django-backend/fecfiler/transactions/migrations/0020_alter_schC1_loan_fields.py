# Generated by Django 4.1.3 on 2023-08-09 14:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("transactions", "0019_schedule_e"),
    ]

    operations = [
        migrations.AlterField(
            model_name="schedulec1",
            name="loan_due_date",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="schedulec1",
            name="loan_interest_rate",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="schedulec1",
            name="line_of_credit",
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
    ]
