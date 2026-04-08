cd django-backend

celery -A fecfiler worker --loglevel=info --pool=gevent --concurrency=100