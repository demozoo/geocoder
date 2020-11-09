#!/bin/bash

PROJECT_NAME=$1
PROJECT_DIR=/home/vagrant/$PROJECT_NAME

# Install essential packages from Apt
apt-get update -y
# Python dev packages
apt-get install -y build-essential python python3-dev python3-pip

pip3 install -r $PROJECT_DIR/requirements.txt

# Set execute permissions on manage.py, as they get lost if we build from a zip file
chmod a+x $PROJECT_DIR/manage.py
