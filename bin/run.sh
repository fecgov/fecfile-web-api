cd django-backend

# Run migrations
./manage.py makemigrations
./manage.py migrate --noinput

# Run application
# python wait_for_db.py &&
gunicorn --bind 0.0.0.0:8080 fecfiler.wsgi -w 10 -t 200 --reload
