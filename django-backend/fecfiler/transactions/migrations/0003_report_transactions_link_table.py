# Generated by Django 4.2.7 on 2024-03-08 16:37

from django.db import migrations, models


def add_link_table(apps, schema_editor):
    transaction = apps.get_model("transactions", "Transaction")

    for t in transaction.objects.all():
        t.reports.add(t.report)
        t.save()


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0006_reporttransaction'),
        ('transactions', '0002_remove_schedulea_contributor_city_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='reports',
            field=models.ManyToManyField(
                through='reports.ReportTransaction',
                to='reports.report'
            ),
        ),
        migrations.RunPython(
            add_link_table,
            migrations.RunPython.noop
        ),
        migrations.RemoveField(
            model_name='transaction',
            name='report'
        ),
    ]
