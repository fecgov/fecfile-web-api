import django.core.validators
from django.db import migrations, models
from django.core.management import call_command


def forwards_func(apps, schema_editor):
    call_command(
        "loaddata",
        "fecfiler/committee_accounts/fixtures/test_db_committee_accounts.json",
    )


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="CommitteeAccount",
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
                ("deleted", models.DateTimeField(blank=True, null=True)),
                (
                    "committee_id",
                    models.CharField(
                        max_length=9,
                        unique=True,
                        validators=[
                            django.core.validators.RegexValidator(
                                "^C[0-9]{8}$", "invalid committee id format"
                            )
                        ],
                    ),
                ),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("updated", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "committee_accounts",
            },
        ),
        migrations.RunPython(forwards_func),
    ]
