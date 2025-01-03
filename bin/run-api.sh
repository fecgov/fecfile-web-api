cd django-backend

# Only Instance 0 runs migrations
echo "------ Starting APP ------"
if [ $CF_INSTANCE_INDEX = "0" ]; then
    echo "----- Migrating Database -----"
    python manage.py migrate --no-input --traceback --verbosity 3
fi

# Run application
exec gunicorn --bind 0.0.0.0:8080 fecfiler.wsgi -w 9
