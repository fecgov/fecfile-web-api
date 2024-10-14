# Updating Committee Views in the Database

When changes are made to the Committee Account model, it is necessary to update
the Committee Views for each committee in the database.  To do this, create a new
migration in the Committee Account app and refer to the following boilerplate code:

```
from django.db import migrations
from fecfiler.committee_accounts.views import create_committee_view

def update_committee_views(apps, schema_editor):
    CommitteeAccount = apps.get_model("committee_accounts", "CommitteeAccount")  # noqa
    for committee in CommitteeAccount.objects.all():
        create_committee_view(committee.id)


class Migration(migrations.Migration):

    dependencies = [(
        'committee_accounts',
        'XXXX_previous_migration_name'
    )]

    operations = [
        migrations.RunPython(
            update_committee_views,
            migrations.RunPython.noop,
        ),
    ]
```
