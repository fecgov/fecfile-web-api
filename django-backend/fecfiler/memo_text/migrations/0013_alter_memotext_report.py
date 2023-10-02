# Generated by Django 4.1.3 on 2023-10-02 16:28

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0002_report'),
        ('memo_text', '0012_alter_memotext_report'),
    ]

    operations = [
        migrations.AlterField(
            model_name='memotext',
            name='report',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='reports.report'),
        ),
    ]