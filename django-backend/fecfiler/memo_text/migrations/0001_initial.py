# Generated by Django 3.2.12 on 2022-07-22 18:39

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('f3x_summaries', '0011_auto_20220609_1730'),
    ]

    operations = [
        migrations.CreateModel(
            name='MemoText',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    primary_key=True,
                    serialize=False,
                    verbose_name='ID'
                    )),
                ('rec_type', models.TextField(blank=True, null=True)),
                ('filer_committee_id_number', models.TextField(
                    blank=True,
                    null=True)),
                ('transaction_id_number', models.TextField(
                    blank=True,
                    null=True)),
                ('back_reference_tran_id_number', models.TextField(
                    blank=True,
                    null=True)),
                ('back_reference_sched_form_name', models.TextField(
                    blank=True,
                    null=True)),
                ('text4000', models.TextField(blank=True, null=True)),
                ('report_id', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    to='f3x_summaries.f3xsummary')),
            ],
            options={
                'db_table': 'memo_text',
            },
        ),
    ]
