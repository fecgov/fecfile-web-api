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
    os.environ["AWS_ACCESS_KEY_ID"] = s3.credentials.get("access_key_id")
    os.environ["AWS_SECRET_ACCESS_KEY"] = s3.credentials.get("secret_access_key")
    os.environ["AWS_STORAGE_BUCKET_NAME"] = s3.credentials.get("bucket")
    os.environ["AWS_REGION"] = s3.credentials.get("region")

if ses:
    os.environ["SES_ACCESS_KEY_ID"] = ses.credentials.get("access_key_id")
    os.environ["SES_SECRET_ACCESS_KEY"] = ses.credentials.get("secret_access_key")
    os.environ["SES_REGION"] = ses.credentials.get("region")
