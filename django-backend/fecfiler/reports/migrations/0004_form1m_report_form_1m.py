# Generated by Django 4.1.3 on 2023-11-06 21:17

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0003_reportf99_report_report_f99'),
    ]

    operations = [
        migrations.CreateModel(
            name='Form1M',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('street_1', models.TextField(blank=True, null=True)),
                ('street_2', models.TextField(blank=True, null=True)),
                ('city', models.TextField(blank=True, null=True)),
                ('state', models.TextField(blank=True, null=True)),
                ('zip', models.TextField(blank=True, null=True)),
                ('committee_type', models.CharField(blank=True, max_length=1, null=True)),
                ('affiliated_date_form_f1_filed', models.DateField(blank=True, null=True)),
                ('affiliated_date_committee_fec_id', models.DateField(blank=True, null=True)),
                ('affiliated_committee_name', models.TextField(blank=True, null=True)),
                ('I_candidate_id_number', models.TextField(blank=True, null=True)),
                ('I_candidate_last_name', models.TextField(blank=True, null=True)),
                ('I_candidate_first_name', models.TextField(blank=True, null=True)),
                ('I_candidate_middle_name', models.TextField(blank=True, null=True)),
                ('I_candidate_prefix', models.TextField(blank=True, null=True)),
                ('I_candidate_suffix', models.TextField(blank=True, null=True)),
                ('I_candidate_office', models.CharField(blank=True, max_length=1, null=True)),
                ('I_candidate_state', models.TextField(blank=True, null=True)),
                ('I_candidate_district', models.TextField(blank=True, null=True)),
                ('I_date_of_contribution', models.DateField(blank=True, null=True)),
                ('II_candidate_id_number', models.TextField(blank=True, null=True)),
                ('II_candidate_last_name', models.TextField(blank=True, null=True)),
                ('II_candidate_first_name', models.TextField(blank=True, null=True)),
                ('II_candidate_middle_name', models.TextField(blank=True, null=True)),
                ('II_candidate_prefix', models.TextField(blank=True, null=True)),
                ('II_candidate_suffix', models.TextField(blank=True, null=True)),
                ('II_candidate_office', models.CharField(blank=True, max_length=1, null=True)),
                ('II_candidate_state', models.TextField(blank=True, null=True)),
                ('II_candidate_district', models.TextField(blank=True, null=True)),
                ('II_date_of_contribution', models.DateField(blank=True, null=True)),
                ('III_candidate_id_number', models.TextField(blank=True, null=True)),
                ('III_candidate_last_name', models.TextField(blank=True, null=True)),
                ('III_candidate_first_name', models.TextField(blank=True, null=True)),
                ('III_candidate_middle_name', models.TextField(blank=True, null=True)),
                ('III_candidate_prefix', models.TextField(blank=True, null=True)),
                ('III_candidate_suffix', models.TextField(blank=True, null=True)),
                ('III_candidate_office', models.CharField(blank=True, max_length=1, null=True)),
                ('III_candidate_state', models.TextField(blank=True, null=True)),
                ('III_candidate_district', models.TextField(blank=True, null=True)),
                ('III_date_of_contribution', models.DateField(blank=True, null=True)),
                ('IV_candidate_id_number', models.TextField(blank=True, null=True)),
                ('IV_candidate_last_name', models.TextField(blank=True, null=True)),
                ('IV_candidate_first_name', models.TextField(blank=True, null=True)),
                ('IV_candidate_middle_name', models.TextField(blank=True, null=True)),
                ('IV_candidate_prefix', models.TextField(blank=True, null=True)),
                ('IV_candidate_suffix', models.TextField(blank=True, null=True)),
                ('IV_candidate_office', models.CharField(blank=True, max_length=1, null=True)),
                ('IV_candidate_state', models.TextField(blank=True, null=True)),
                ('IV_candidate_district', models.TextField(blank=True, null=True)),
                ('IV_date_of_contribution', models.DateField(blank=True, null=True)),
                ('V_candidate_id_number', models.TextField(blank=True, null=True)),
                ('V_candidate_last_name', models.TextField(blank=True, null=True)),
                ('V_candidate_first_name', models.TextField(blank=True, null=True)),
                ('V_candidate_middle_name', models.TextField(blank=True, null=True)),
                ('V_candidate_prefix', models.TextField(blank=True, null=True)),
                ('V_candidate_suffix', models.TextField(blank=True, null=True)),
                ('V_candidate_office', models.CharField(blank=True, max_length=1, null=True)),
                ('V_candidate_state', models.TextField(blank=True, null=True)),
                ('V_candidate_district', models.TextField(blank=True, null=True)),
                ('V_date_of_contribution', models.DateField(blank=True, null=True)),
            ],
        ),
        migrations.AddField(
            model_name='report',
            name='form_1m',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='reports.form1m'),
        ),
    ]
