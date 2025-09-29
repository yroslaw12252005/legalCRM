#!/bin/bash
cd /opt/build
python manage.py collectstatic --noinput
python manage.py migrate
gunicorn --bind 0.0.0.0:8000 legalCRM.wsgi:application 

# Use PORT environment variable if available, otherwise default to 8000
PORT=${PORT:-8000}
gunicorn --bind 0.0.0.0:$PORT legalCRM.wsgi:application