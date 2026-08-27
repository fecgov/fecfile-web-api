cd django-backend

echo "------ Starting APP ------"

# Run application
./manage.py collectstatic --noinput --traceback --verbosity 3 && exec gunicorn --bind 0.0.0.0:8080 fecfiler.wsgi -w 9 --threads=8
