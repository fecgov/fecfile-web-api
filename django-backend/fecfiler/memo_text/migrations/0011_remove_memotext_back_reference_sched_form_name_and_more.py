# Generated by Django 4.1.3 on 2023-05-03 20:57

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('memo_text', '0010_remove_memotext_filer_committee_id_number'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='memotext',
            name='back_reference_sched_form_name',
        ),
        migrations.RemoveField(
            model_name='memotext',
            name='back_reference_tran_id_number',
        ),
    ]
