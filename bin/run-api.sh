cd django-backend

# Run migrations
./manage.py migrate --noinput --check --traceback > migrate.out

# Run application
python wait_for_db.py && gunicorn --bind 0.0.0.0:8080 fecfiler.wsgi -w 9 -t 200
