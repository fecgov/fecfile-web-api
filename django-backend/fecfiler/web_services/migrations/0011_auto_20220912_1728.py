# Generated by Django 3.2.12 on 2022-09-12 21:28

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('web_services', '0010_auto_20220912_1716'),
    ]

    operations = [
        migrations.RenameField(
            model_name='uploadsubmission',
            old_name='dot_fec',
            new_name='dot_fec_old',
        ),
        migrations.RenameField(
            model_name='webprintsubmission',
            old_name='dot_fec',
            new_name='dot_fec_old',
        ),
    ]
