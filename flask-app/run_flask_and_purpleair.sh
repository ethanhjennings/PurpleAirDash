#!/bin/bash

# Wrapper script so we can run both the flask server and purpleair_proxy from a single container
# TODO: Split off purpleair_proxy into its own container and delete this script

# Substitute in html because we don't have a proper templating engine.
# TODO: Add templating engine?
grep -rl '${DOMAIN_NAME}' . | xargs sed -i 's/${DOMAIN_NAME}/'"$DOMAIN_NAME"'/g'
grep -rl '${SCRIPT_NAME}' . | xargs sed -i 's/${SCRIPT_NAME}/'"$SCRIPT_NAME"'/g'
grep -rl '${MAPBOX_API_KEY}' . | xargs sed -i 's/${MAPBOX_API_KEY}/'"$MAPBOX_API_KEY"'/g'

# Copy edited static content to volume so that it's available to nginx
rm -rf static-nginx/*
cp -r static/* static-nginx/

# Start flask
gunicorn --workers=4 --bind=0.0.0.0:5000 app:app &

# Start purpleair_proxy
cd purpleair_proxy; python3 purpleair_proxy.py

# Wait for processes
wait -n

# Exit with status of process that exited first
exit $?
