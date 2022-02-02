cd django-backend

# Run migrations
./manage.py makemigrations
./manage.py migrate --noinput

# Run application
gunicorn --bind 0.0.0.0:8080 fecfiler.wsgi -w 10 -t 200 --reload
