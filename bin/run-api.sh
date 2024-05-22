cd django-backend

echo2 =======================test &&
	gunicorn --bind 0.0.0.0:8080 fecfiler.wsgi -w 9
