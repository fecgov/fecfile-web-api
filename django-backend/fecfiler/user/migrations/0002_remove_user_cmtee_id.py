# Generated by Django 4.2.7 on 2024-01-25 14:53

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("user", "0001_initial"),
        ("committee_accounts", "0002_membership"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="user",
            name="cmtee_id",
        ),
        migrations.AlterField(
            model_name="user",
            name="first_name",
            field=models.CharField(blank=True, max_length=150, null=True),
        ),
        migrations.AlterField(
            model_name="user",
            name="last_name",
            field=models.CharField(blank=True, max_length=150, null=True),
        ),
    ]
