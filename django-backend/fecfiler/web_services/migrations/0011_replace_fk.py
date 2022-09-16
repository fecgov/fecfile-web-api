# Generated by Django 3.2.12 on 2022-09-12 21:31

from django.db import migrations, models
import django.db.models.deletion


def update_uuid(apps, schema_editor):
    DotFEC = apps.get_model("web_services", "DotFEC")  # noqa
    UploadSubmission = apps.get_model("web_services", "UploadSubmission")  # noqa
    WebPrintSubmission = apps.get_model("web_services", "WebPrintSubmission")  # noqa
    dot_fec_uuid = DotFEC.objects.filter(id=models.OuterRef("dot_fec_old")).values_list(
        "uuid"
    )[:1]
    UploadSubmission.objects.update(dot_fec=models.Subquery(dot_fec_uuid))
    WebPrintSubmission.objects.update(dot_fec=models.Subquery(dot_fec_uuid))


class Migration(migrations.Migration):

    dependencies = [
        ("web_services", "0010_remove_fk_uuid_to_pk"),
    ]

    operations = [
        migrations.AddField(
            model_name="uploadsubmission",
            name="dot_fec",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="web_services.dotfec",
            ),
        ),
        migrations.AddField(
            model_name="webprintsubmission",
            name="dot_fec",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="web_services.dotfec",
            ),
        ),
        migrations.RunPython(update_uuid),
        migrations.RemoveField(
            model_name="dotfec",
            name="id",
        ),
        migrations.RemoveField(
            model_name="uploadsubmission",
            name="dot_fec_old",
        ),
        migrations.RemoveField(
            model_name="webprintsubmission",
            name="dot_fec_old",
        ),
    ]
