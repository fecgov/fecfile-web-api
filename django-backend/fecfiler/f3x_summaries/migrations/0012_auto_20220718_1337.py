# Generated by Django 3.2.12 on 2022-07-18 17:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('f3x_summaries', '0011_auto_20220609_1730'),
    ]

    operations = [
        migrations.AddField(
            model_name='f3xsummary',
            name='confirmation_email_1',
            field=models.EmailField(blank=True, default=None, max_length=44, null=True),
        ),
        migrations.AddField(
            model_name='f3xsummary',
            name='confirmation_email_2',
            field=models.EmailField(blank=True, default=None, max_length=44, null=True),
        ),
    ]