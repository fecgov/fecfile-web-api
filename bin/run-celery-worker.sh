#!/bin/sh
# Dockerfile entrypoint
# Exit immediately if a command exits with a non-zero status.
set -e

exec celery -A fecfiler worker --loglevel=info --pool=threads