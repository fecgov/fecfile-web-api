from django.db import migrations
from django.db.models import Q


def remove_old_login_accounts(apps, schema_editor):
    User = apps.get_model("user", "User")  # noqa
    Membership = apps.get_model("committee_accounts", "Membership")  # noqa

    user_ids_to_delete = User.objects.filter(
        ~Q(username__contains="%-%-%-%-%")
    ).values_list("id", flat=True)
    Membership.objects.filter(user_id__in=user_ids_to_delete).delete()
    User.objects.filter(id__in=user_ids_to_delete).delete()


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
