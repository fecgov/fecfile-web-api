#!/bin/sh
# Dockerfile entrypoint
# Exit immediately if a command exits with a non-zero status.
set -e

# Run database migrations
echo "Running migrations..."
python manage.py migrate

# Conditionally run collectstatic
if [ "$FECFILE_SILK_ENABLED" = "1" ] || [ "$FECFILE_SILK_ENABLED" = "true" ] || [ "$FECFILE_SILK_ENABLED" = "True" ] || [ "$INCLUDE_SILK" = "True" ]; then
  echo "Silk is enabled, running collectstatic..."
  python manage.py collectstatic --no-input
else
  echo "Silk is not enabled, skipping collectstatic."
fi

# Load application data
echo "Loading initial data..."
python manage.py loaddata fixtures/user-data.json
python manage.py load_mocked_committee_data

# Start the Gunicorn server
echo "Starting Gunicorn server..."
exec gunicorn --bind 0.0.0.0:8080 fecfiler.wsgi -w 9 --threads=8 --reload
