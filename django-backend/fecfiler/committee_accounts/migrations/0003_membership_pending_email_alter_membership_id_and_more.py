# Generated by Django 4.2.7 on 2024-02-16 20:43

from django.conf import settings
from django.db import migrations, models
from django.utils import timezone
import uuid


def delete_pending_memberships(apps, schema_editor):
    Membership = apps.get_model("committee_accounts", "Membership")  # noqa
    Membership.objects.filter(user=None).delete()


def generate_new_uuid(apps, schema_editor):
    Membership = apps.get_model("committee_accounts", "Membership")  # noqa
    for membership in Membership.objects.all():
        membership.uuid = uuid.uuid4()
        membership.save()


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('committee_accounts', '0002_membership'),
    ]

    operations = [
        migrations.AddField(
            model_name='membership',
            name='pending_email',
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
        migrations.AddField(
            model_name='membership',
            name='uuid',
            field=models.UUIDField(
                default=uuid.uuid4,
                editable=False,
                primary_key=False,
                serialize=False,
                unique=False
            )
        ),
        migrations.RunPython(
            generate_new_uuid,
            migrations.RunPython.noop,
        ),
        migrations.RemoveField(
            model_name='membership',
            name='id',
        ),
        migrations.RenameField(
            model_name='membership',
            old_name='uuid',
            new_name='id'
        ),
        migrations.AlterField(
            model_name='membership',
            name='id',
            field=models.UUIDField(
                default=uuid.uuid4,
                editable=False,
                primary_key=True,
                serialize=False,
                unique=True
            )
        ),
        migrations.AlterField(
            model_name='membership',
            name='user',
            field=models.ForeignKey(
                null=True,
                on_delete=models.deletion.CASCADE,
                to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AddField(
            model_name='membership',
            name='created',
            field=models.DateTimeField(auto_now_add=True, default=timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='membership',
            name='updated',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.RunPython(
            migrations.RunPython.noop,
            delete_pending_memberships
        ),
    ]