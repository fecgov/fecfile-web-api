# Generated by Django 4.2.7 on 2024-01-15 20:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0003_update_f24_amendment_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='form1m',
            name='date_committee_met_requirements',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='form1m',
            name='date_of_51st_contributor',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='form1m',
            name='date_of_original_registration',
            field=models.DateField(blank=True, null=True),
        ),
    ]
