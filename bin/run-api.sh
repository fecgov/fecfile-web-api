cd django-backend

# Run migrations and application
./manage.py migrate --no-input --traceback --verbosity 3 &&
	exec gunicorn --bind 0.0.0.0:8080 fecfiler.wsgi -w 9
