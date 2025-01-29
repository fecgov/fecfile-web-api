cd django-backend

exit 0

# Only Instance 0 runs migrations and creates views
echo "------ Starting APP ------"
if [ $CF_INSTANCE_INDEX = "0" ]; then
    echo "----- Creating committee views -----"
    python manage.py create_committee_views
fi

# Run application
exec gunicorn --bind 0.0.0.0:8080 fecfiler.wsgi -w 9 --threads=8
