# Generated by Django 4.1.3 on 2023-10-02 22:05

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0002_report'),
    ]

    operations = [
        migrations.RenameField(
            model_name='report',
            old_name='form_type',
            new_name='_form_type',
        ),
    ]
