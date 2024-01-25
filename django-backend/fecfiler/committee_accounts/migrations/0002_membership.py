# Generated by Django 4.2.7 on 2024-01-25 14:11

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.contrib.auth.validators
import django.utils.timezone


def create_memberships(apps, schema_editor):
    CommitteeAccount = apps.get_model("committee_accounts", "CommitteeAccount")
    User = apps.get_model("user", "User")
    Membership = apps.get_model("committee_accounts", "Membership")
    db_alias = schema_editor.connection.alias
    users = User.objects.using(db_alias).all()
    for user in users:
        committee = CommitteeAccount.get(committee_id=user.cmtee_id)
        membership = Membership(
            user=user,
            committee_account=committee,
            role=Membership.CommitteeRole.COMMITTEE_ADMINISTRATOR,
        )
        membership.save()


class Migration(migrations.Migration):
    dependencies = [
        ("user", "0001_initial"),
        ("committee_accounts", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Membership",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "role",
                    models.CharField(
                        choices=[
                            ("COMMITTEE_ADMINISTRATOR", "Committee Administrator"),
                            ("REVIEWER", "Reviewer"),
                        ],
                        max_length=25,
                    ),
                ),
                (
                    "committee_account",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="committee_accounts.committeeaccount",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="user.user"
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="committeeaccount",
            name="members",
            field=models.ManyToManyField(
                through="committee_accounts.Membership", to="user.User"
            ),
        ),
        migrations.RunPython(create_memberships),
    ]
