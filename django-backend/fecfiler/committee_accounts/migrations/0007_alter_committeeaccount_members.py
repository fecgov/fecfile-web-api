# Generated by Django 5.2 on 2025-04-30 17:10

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('committee_accounts', '0006_alter_membership_committee_account_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='committeeaccount',
            name='members',
            field=models.ManyToManyField(
                through='committee_accounts.Membership',
                through_fields=('committee_account', 'user'),
                to=settings.AUTH_USER_MODEL
            ),
        ),
    ]
