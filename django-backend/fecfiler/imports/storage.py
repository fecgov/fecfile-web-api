from fecfiler.settings import (
    UPLOAD_STORAGE_TYPE,
    UploadStorageType,
    S3_STORAGE_BUCKET_NAME,
    UPLOAD_LOCAL_STORAGE_DIRECTORY,
)

from fecfiler.s3 import S3_SESSION
import os


# Should refactor this and web_service_storage to use a common storage interface
def save_upload(file):
    if UPLOAD_STORAGE_TYPE == UploadStorageType.LOCAL:
        if not os.path.exists(UPLOAD_LOCAL_STORAGE_DIRECTORY):
            os.makedirs(UPLOAD_LOCAL_STORAGE_DIRECTORY)
        file_path = os.path.join(UPLOAD_LOCAL_STORAGE_DIRECTORY, file.name)
        with open(file_path, "wb") as f:
            for chunk in file.chunks():
                f.write(chunk)
        return file.name
    elif UPLOAD_STORAGE_TYPE == UploadStorageType.S3:
        bucket = S3_SESSION.Bucket(S3_STORAGE_BUCKET_NAME)
        bucket.upload_fileobj(file, file.name)
        return file.name
    else:
        raise ValueError(f"Unsupported upload storage type: {UPLOAD_STORAGE_TYPE}")
