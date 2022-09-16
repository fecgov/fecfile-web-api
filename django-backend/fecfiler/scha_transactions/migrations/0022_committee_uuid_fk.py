# Generated by Django 3.2.12 on 2022-09-09 16:41

from django.db import migrations, models


def update_uuid(apps, schema_editor):
    SchATransaction = apps.get_model("scha_transactions", "SchATransaction")  # noqa
    CommitteeAccount = apps.get_model("committee_accounts", "CommitteeAccount")  # noqa
    committee_uuid = CommitteeAccount.objects.filter(
        id=models.OuterRef("committee_account_old")
    ).values_list("uuid")[:1]
    SchATransaction.objects.update(committee_account=models.Subquery(committee_uuid))


class Migration(migrations.Migration):

    dependencies = [
        ("scha_transactions", "0021_committee_fk_to_int"),
        ("committee_accounts", "0003_uuid_pk"),
    ]

    operations = [
        migrations.RenameField(
            model_name="schatransaction",
            old_name="committee_account",
            new_name="committee_account_old",
        ),
        migrations.AddField(
            model_name="schatransaction",
            name="committee_account",
            field=models.ForeignKey(
                null=True,
                on_delete=models.deletion.CASCADE,
                to="committee_accounts.CommitteeAccount",
            ),
        ),
        migrations.RunPython(update_uuid),
        migrations.RemoveField(
            model_name="schatransaction",
            name="committee_account_old",
        ),
    ]
