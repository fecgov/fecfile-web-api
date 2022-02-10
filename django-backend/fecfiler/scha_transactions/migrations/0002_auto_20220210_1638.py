# Generated by Django 3.2.11 on 2022-02-10 21:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scha_transactions', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='schatransaction',
            name='contribution_date',
            field=models.CharField(blank=True, max_length=8, null=True),
        ),
        migrations.AlterField(
            model_name='schatransaction',
            name='created',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='schatransaction',
            name='donor_candidate_district',
            field=models.CharField(blank=True, max_length=2, null=True),
        ),
        migrations.AlterField(
            model_name='schatransaction',
            name='updated',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
