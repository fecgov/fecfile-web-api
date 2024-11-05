cd django-backend

# Run migrations and application
./manage.py migrate --no-input --traceback --verbosity 3 &&
	python manage.py create_committee_views &&
	exec gunicorn --bind 0.0.0.0:8080 fecfiler.wsgi -w 9
# run create_committee_views to trigger their update if the view definition has changed