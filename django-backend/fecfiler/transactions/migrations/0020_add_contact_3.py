from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("contacts", "0011_alter_contact_id"),
        ("transactions", "0019_alter_schC1_loan_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="transaction",
            name="contact_3",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="contact_3_transaction_set",
                to="contacts.contact",
            ),
        )
    ]
