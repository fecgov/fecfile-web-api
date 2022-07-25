from io import BytesIO
from pathlib import Path
from fecfiler.settings import (
    CELERY_WORKER_STORAGE,
    AWS_STORAGE_BUCKET_NAME,
    CELERY_LOCAL_STORAGE_DIRECTORY,
)
from fecfiler.s3 import S3_SESSION
from fecfiler.celery import CeleryStorageType
import logging

logger = logging.getLogger(__name__)


def store_file(file_content, file_name, force_write_to_disk=False):
    if CELERY_WORKER_STORAGE == CeleryStorageType.AWS and not force_write_to_disk:
        logger.info(f"uploading file to s3: {file_name}")
        s3_object = S3_SESSION.Object(AWS_STORAGE_BUCKET_NAME, file_name)
        s3_object.put(Body=file_content.encode("utf-8"))
        logger.info(f"SUCCESS file was uploaded s3: {file_name}")
    else:
        logger.info(f"writing file to disk: {file_name}")
        path = Path(CELERY_LOCAL_STORAGE_DIRECTORY) / file_name
        with open(path, "w", encoding="utf-8") as file:
            file.write(file_content)
            logger.info(f"SUCCESS file was written to disk: {file_name}")


def get_file(file_name, force_read_from_disk=False):
    if CELERY_WORKER_STORAGE == CeleryStorageType.AWS and not force_read_from_disk:
        logger.info(f"retrieving file from s3: {file_name}")
        s3_object = S3_SESSION.Object(AWS_STORAGE_BUCKET_NAME, file_name)
        file = s3_object.get()["Body"]
        logger.info(f"SUCCESS file was retrieved s3: {file_name}")
    else:
        logger.info(f"retrieving file from disk: {file_name}")
        path = Path.joinpath(CELERY_LOCAL_STORAGE_DIRECTORY, file_name)
        file = open(path, encoding="utf-8")
        logger.info(f"SUCCESS file was retrieved disk: {file_name}")
    return file
