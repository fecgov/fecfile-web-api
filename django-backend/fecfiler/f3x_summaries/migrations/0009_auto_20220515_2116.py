# Generated by Django 3.2.12 on 2022-05-16 01:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('f3x_summaries', '0008_auto_20220503_1411'),
    ]

    operations = [
        migrations.AlterField(
            model_name='f3xsummary',
            name='change_of_address',
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
        migrations.AlterField(
            model_name='f3xsummary',
            name='qualified_committee',
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
    ]
