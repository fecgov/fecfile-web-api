"""Django App for FECFile API
"""
from .celery import app as celery_app
import boto3
from django.conf import settings

""" This will make sure the app is always imported when
Django starts so that shared_task will use this app.
"""
__all__ = ("celery_app",)

if settings.CELERY_WORKER_STORAGE == settings.CeleryStorageType.AWS:
    session = boto3.session.Session()
    S3_SESSION = session.resource(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION,
    )
else:
    S3_SESSION = None
