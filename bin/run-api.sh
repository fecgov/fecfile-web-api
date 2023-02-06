cd django-backend

# Run migrations and application
./manage.py migrate --no-input --traceback --verbosity 3 > migrate.out &&
	python wait_for_db.py && 
	gunicorn --bind 0.0.0.0:8080 fecfiler.wsgi -w 9
