cd django-backend

celery -A fecfiler worker --loglevel=info --pool=threads --concurrency=$CELERY_WORKER_CONCURRENCY