# Generated by Django 4.2.7 on 2024-04-19 15:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0008_form3x_committee_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='form24',
            name='committee_name',
            field=models.TextField(blank=True, null=True),
        ),
    ]