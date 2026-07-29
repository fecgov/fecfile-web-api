import boto3
from fecfiler.settings import S3_ACCESS_KEY_ID, S3_SECRET_ACCESS_KEY, S3_REGION

if S3_ACCESS_KEY_ID and S3_SECRET_ACCESS_KEY and S3_REGION:
    session = boto3.session.Session()
    S3_SESSION = session.resource(
        "s3",
        aws_access_key_id=S3_ACCESS_KEY_ID,
        aws_secret_access_key=S3_SECRET_ACCESS_KEY,
        region_name=S3_REGION,
    )
else:
    S3_SESSION = None
