# Generated by Django 5.1.7 on 2025-03-26 14:54

from django.db import migrations, models
import django_migration_linter as linter


class Migration(migrations.Migration):

    dependencies = [
        ("transactions", "0017_schedulef_coordianted_to_coordinated"),
    ]

    operations = [
        linter.IgnoreMigration(),
        migrations.AddField(
            model_name="schedulef",
            name="general_election_year",
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name="schedulef",
            name="category_code",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="schedulef",
            name="memo_text_description",
            field=models.TextField(blank=True, null=True),
        ),
    ]
