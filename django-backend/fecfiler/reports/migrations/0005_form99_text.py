# Generated by Django 4.1.3 on 2023-11-22 13:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0004_form1m_report_form_1m'),
    ]

    operations = [
        migrations.AddField(
            model_name='form99',
            name='text',
            field=models.TextField(blank=True, null=True),
        ),
    ]