import cfenv
import os

env = cfenv.AppEnv()

redis = env.get_service(name="fecfile-api-redis")
s3 = env.get_service(name="fecfile-api-s3")
ses = env.get_service(name="fecfile-api-ses")

if redis:
    password = redis.credentials.get("password")
    hostname = redis.credentials.get("hostname")
    port = redis.credentials.get("port")
    os.environ["REDIS_URL"] = f"rediss://:{password}@{hostname}:{port}"

if s3:
    os.environ["S3_ACCESS_KEY_ID"] = s3.credentials.get("access_key_id")
    os.environ["S3_SECRET_ACCESS_KEY"] = s3.credentials.get("secret_access_key")
    os.environ["S3_REGION"] = s3.credentials.get("region")
    os.environ["S3_STORAGE_BUCKET_NAME"] = s3.credentials.get("bucket")

if ses:
    os.environ["SES_ACCESS_KEY_ID"] = ses.credentials.get("aws_access_key_id")
    os.environ["SES_SECRET_ACCESS_KEY"] = ses.credentials.get("aws_secret_access_key")
    os.environ["SES_REGION"] = ses.credentials.get("region")
