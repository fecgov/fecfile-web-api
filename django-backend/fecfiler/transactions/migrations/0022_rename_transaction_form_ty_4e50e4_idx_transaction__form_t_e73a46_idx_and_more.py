# Generated by Django 4.1.3 on 2023-09-18 20:57

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '__first__'),
        ('transactions', '0021_remove_loan_ptd_balance'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transaction',
            name='report',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='reports.f3xreport'),
        ),
    ]
