# Generated by Django 3.2.11 on 2022-02-11 21:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('f3x_summaries', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='f3xsummary',
            name='deleted',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
