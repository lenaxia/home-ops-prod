#!/bin/sh

if [ ! -e "config/config.yaml" ]; then
    echo "Resource not found, copying from defaults: config.yaml"
    cp -r "default/config.yaml" "config/config.yaml"
fi

# Start the server
exec node server.js --host 0.0.0.0 --port 8000
