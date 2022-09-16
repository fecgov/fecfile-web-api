# Generated by Django 3.2.12 on 2022-09-09 16:41

from django.db import migrations, models


def update_uuid(apps, schema_editor):
    MemoText = apps.get_model("memo_text", "MemoText")  # noqa
    CommitteeAccount = apps.get_model("committee_accounts", "CommitteeAccount")  # noqa
    committee_uuid = CommitteeAccount.objects.filter(
        id=models.OuterRef("committee_account_old")
    ).values_list("uuid")[:1]
    MemoText.objects.update(committee_account=models.Subquery(committee_uuid))


class Migration(migrations.Migration):

    dependencies = [
        ("memo_text", "0005_committee_fk_to_int"),
        ("committee_accounts", "0003_uuid_pk"),
    ]

    operations = [
        migrations.RenameField(
            model_name="memotext",
            old_name="committee_account",
            new_name="committee_account_old",
        ),
        migrations.AddField(
            model_name="memotext",
            name="committee_account",
            field=models.ForeignKey(
                null=True,
                on_delete=models.deletion.CASCADE,
                to="committee_accounts.CommitteeAccount",
            ),
        ),
        migrations.RunPython(update_uuid),
        migrations.RemoveField(
            model_name="memotext",
            name="committee_account_old",
        ),
    ]
