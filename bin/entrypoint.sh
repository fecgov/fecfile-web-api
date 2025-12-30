#!/bin/sh
# Dockerfile entrypoint
# Exit immediately if a command exits with a non-zero status.
set -e

# Run database migrations
echo "Running migrations..."
python manage.py migrate

# Conditionally run collectstatic
if [ "$INCLUDE_SILK" = "True" ]; then
  echo "INCLUDE_SILK is True, running collectstatic..."
  python manage.py collectstatic --no-input
else
  echo "INCLUDE_SILK is not 'True', skipping collectstatic."
fi

# Load application data
echo "Loading initial data..."
python manage.py loaddata fixtures/user-data.json
python manage.py load_mocked_committee_data
python manage.py gen_locust_load_test_data #--number_of_committees 1 --number_of_contacts 1

# Start the Gunicorn server
echo "Starting Gunicorn server..."
exec gunicorn --bind 0.0.0.0:8080 fecfiler.wsgi -w 9 --threads=8 --reload