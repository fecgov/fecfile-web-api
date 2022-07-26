import cfenv
import os
import ssl

env = cfenv.AppEnv()

redis = env.get_service(name="fecfile-api-redis")
s3 = env.get_service(name="fecfile-api-s3")

if redis:
    os.environ["REDIS_URL"] = redis.credentials.get("uri")
    os.environ["CELERY_BROKER_USE_SSL"] = {"ssl_cert_reqs": ssl.CERT_NONE}
    os.environ["CELERY_REDIS_BACKEND_USE_SSL"] = {"ssl_cert_reqs": ssl.CERT_NONE}

if s3:
    os.environ["AWS_ACCESS_KEY_ID"] = s3.credentials.get("access_key_id")
    os.environ["AWS_SECRET_ACCESS_KEY"] = s3.credentials.get("secret_access_key")
    os.environ["AWS_STORAGE_BUCKET_NAME"] = s3.credentials.get("bucket")
    os.environ["AWS_REGION"] = s3.credentials.get("region")
