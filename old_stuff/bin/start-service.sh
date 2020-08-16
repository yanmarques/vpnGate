#!/bin/sh
if [ -z "$1" ]; then
    echo "Missing argument: application name"
fi

if [ -z "$2" ]; then
    echo "Missing argument: environment"
fi

APP_NAME="$1"
ENV_FILE="$2"
shift
shift

if [ ! -f "$ENV_FILE" ]; then
    cp .env.example "$ENV_FILE"

    export FLASK_APP="$APP_NAME:create_app()"
    flask gen:key "$ENV_FILE"
fi 

dotenv -f "$ENV_FILE" -q never set FLASK_DEBUG 0 
dotenv -f "$ENV_FILE" set FLASK_ENV production
dotenv -f "$ENV_FILE" set FLASK_RUN_HOST 0.0.0.0

APP_WSGI="$APP_NAME" gunicorn wsgi:app "$@"