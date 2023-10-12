from django.db import migrations
from django.contrib.contenttypes import management


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("transactions", "0003_schedulea_transaction"),
    ]

    operations = []
