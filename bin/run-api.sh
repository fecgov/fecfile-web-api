cd django-backend

echo "------ Starting APP ------"

# Run application
exec gunicorn --bind 0.0.0.0:8080 fecfiler.wsgi -w 9 --threads=7
