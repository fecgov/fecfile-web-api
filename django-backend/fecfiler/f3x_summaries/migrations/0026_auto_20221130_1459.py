# Generated by Django 3.2.12 on 2022-11-30 19:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('f3x_summaries', '0025_auto_20220915_1309'),
    ]

    operations = [
        migrations.AlterField(
            model_name='f3xsummary',
            name='report_code',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.DeleteModel(
            name='ReportCodeLabel',
        ),
    ]