#!/bin/bash

echo "Starting installation of requirements..."
pip install -r requirements.txt
echo "Requirements installed."
apt-get install -y unixodbc-dev gcc g++ python3-dev libffi-dev libssl-dev portaudio19-dev
echo "Starting the application..."
exec gunicorn --bind 0.0.0.0:$PORT app:app
