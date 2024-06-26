from django.db import migrations
from django.db.models import Q


def remove_old_login_accounts(apps, schema_editor):
    User = apps.get_model("user", "User")  # noqa

    users_to_delete = User.objects.filter(
        Q(username__contains="@") | Q(username="adminnxg") | Q(username="tt")
    )
    for user in users_to_delete:
        user.membership_set.all().delete()
    users_to_delete.delete()


class Migration(migrations.Migration):

    dependencies = [
        (
            "user",
            "0005_rename_security_consent_date_user_security_consent_exp_date",
        )
    ]

    operations = [
        migrations.RunPython(
            remove_old_login_accounts,
            migrations.RunPython.noop,
        ),
    ]
