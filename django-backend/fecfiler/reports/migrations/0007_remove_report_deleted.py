# Generated by Django 4.2.10 on 2024-04-05 15:04

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0006_reporttransaction'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='report',
            name='deleted',
        ),
    ]
