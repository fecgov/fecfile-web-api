# Generated by Django 4.1.3 on 2023-10-13 15:54

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0001_initial'),
        ('memo_text', '0011_remove_memotext_back_reference_sched_form_name_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='memotext',
            name='report',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='reports.report'),
        ),
    ]