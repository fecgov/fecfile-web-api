from fecfiler.settings import SYSTEM_STATUS_CACHE_BACKEND, SYSTEM_STATUS_CACHE_AGE
import json
import redis
import structlog

logger = structlog.get_logger(__name__)
if SYSTEM_STATUS_CACHE_BACKEND:
    redis_instance = redis.Redis.from_url(SYSTEM_STATUS_CACHE_BACKEND)
else:
    raise SystemError("SYSTEM_STATUS_CACHE_BACKEND is not set")


def get_redis_value(key):
    """
    Get value from redis and parse the json.
    If they value is falsy ("", None), return None
    """
    value = redis_instance.get(key)
    return json.loads(value) if value else None


def set_redis_value(key, value, age=SYSTEM_STATUS_CACHE_AGE):
    """
    Set redis value and parse the json.
    If they value is falsy ("", None), return None
    """
    redis_instance.set(key, json.dumps(value), ex=age)


def refresh_cache(key, method):
    """
    First set the cache value to an empty dictionary to indicate that the status is
    being checked.  Then run the method to get the status and update the cache with
    the result. The empty dictionary value keeps us from checking the status multiple
    times if the cache expires.
    """
    redis_instance.set(key, json.dumps({}), ex=SYSTEM_STATUS_CACHE_AGE)
    status = method()
    redis_instance.set(key, json.dumps(status), ex=SYSTEM_STATUS_CACHE_AGE)
    return status
