#!/bin/sh
# Dockerfile entrypoint
# Exit immediately if a command exits with a non-zero status.
set -e

# Run database migrations
echo "Running migrations..."
python manage.py migrate

# Conditionally run collectstatic
case "$(printf '%s' "$FECFILE_SILK_ENABLED" | tr '[:upper:]' '[:lower:]')" in
  true|1|yes|y)
  echo "FECFILE_SILK_ENABLED is True, running collectstatic..."
  python manage.py collectstatic --no-input
  ;;
*)
  echo "FECFILE_SILK_ENABLED is not 'True', skipping collectstatic."
  ;;
esac

# Load application data
echo "Loading initial data..."
python manage.py loaddata fixtures/user-data.json
python manage.py load_mocked_committee_data

# Start the Gunicorn server
echo "Starting Gunicorn server..."
exec gunicorn --bind 0.0.0.0:8080 fecfiler.wsgi -w 9 --threads=8 --reload
