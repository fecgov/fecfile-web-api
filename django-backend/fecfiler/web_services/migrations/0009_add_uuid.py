# Generated by Django 3.2.12 on 2022-09-09 16:41

from django.db import migrations, models
import uuid


def create_uuid(apps, schema_editor):
    DotFEC = apps.get_model("web_services", "DotFEC")  # noqa
    for dotfec in DotFEC.objects.all():
        dotfec.uuid = uuid.uuid4()
        dotfec.save()
    UploadSubmission = apps.get_model("web_services", "UploadSubmission")  # noqa
    for uploadsubmission in UploadSubmission.objects.all():
        uploadsubmission.uuid = uuid.uuid4()
        uploadsubmission.save()
    WebPrintSubmission = apps.get_model("web_services", "WebPrintSubmission")  # noqa
    for webprintsubmission in WebPrintSubmission.objects.all():
        webprintsubmission.uuid = uuid.uuid4()
        webprintsubmission.save()


class Migration(migrations.Migration):

    dependencies = [
        ("web_services", "0008_webprintsubmission_fec_image_url"),
    ]

    operations = [
        migrations.AddField(
            model_name="dotfec",
            name="uuid",
            field=models.UUIDField(default=uuid.uuid4, editable=False),
        ),
        migrations.AddField(
            model_name="uploadsubmission",
            name="uuid",
            field=models.UUIDField(default=uuid.uuid4, editable=False),
        ),
        migrations.AddField(
            model_name="webprintsubmission",
            name="uuid",
            field=models.UUIDField(default=uuid.uuid4, editable=False),
        ),
        migrations.RunPython(create_uuid, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="dotfec",
            name="uuid",
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
        migrations.AlterField(
            model_name="uploadsubmission",
            name="uuid",
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
        migrations.AlterField(
            model_name="webprintsubmission",
            name="uuid",
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
    ]
