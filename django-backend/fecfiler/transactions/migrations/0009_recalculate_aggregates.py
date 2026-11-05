from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("transactions", "0008_remove_s_from_refund_type"),
    ]

    operations = [
        # This migration called save on the Transaction model for the start of
        # each transaction chain in order to update the entity aggregate values
        # for all transactions.  It imported the Transaction model and manager
        # in order to do this.
        #
        # Since the importing of migrations in models is problematic and since
        # this migration already ran in all the environments and is not needed in
        # new database instances, we removed this as it was causing issues when
        # adding additional migrations to the model locally.
        #
        # The issue is detailed in the Django documentation:
        # https://docs.djangoproject.com/en/6.1/topics/migrations/#historical-models
        #
        # The original migration can be found here:
        # https://github.com/fecgov/fecfile-web-api/blob/071b727dd40ee647d6128ebc522ec23a1bd55298/django-backend/fecfiler/transactions/migrations/0009_recalculate_aggregates.py
    ]
