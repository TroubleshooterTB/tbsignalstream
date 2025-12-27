#!/bin/sh
# Wrapper script to ensure Python can find modules
cd /app
export PYTHONPATH=/app:$PYTHONPATH
exec gunicorn --bind 0.0.0.0:8080 --workers 1 --threads 4 --timeout 0 --chdir /app main:app
