# Generated by Django 3.2.12 on 2022-09-15 17:09

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('web_services', '0013_remove_id_after_f3x'),
    ]

    operations = [
        migrations.RenameField(
            model_name='dotfec',
            old_name='uuid',
            new_name='id',
        ),
        migrations.RenameField(
            model_name='uploadsubmission',
            old_name='uuid',
            new_name='id',
        ),
        migrations.RenameField(
            model_name='webprintsubmission',
            old_name='uuid',
            new_name='id',
        ),
    ]
