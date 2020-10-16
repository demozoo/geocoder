#!/bin/bash

# Script to set up a Django project on Vagrant.

# Installation settings

PROJECT_NAME=$1

DB_NAME=$PROJECT_NAME
VIRTUALENV_NAME=$PROJECT_NAME

PROJECT_DIR=/home/vagrant/$PROJECT_NAME
VIRTUALENV_DIR=/home/vagrant/.virtualenvs/$PROJECT_NAME
LOCAL_SETTINGS_PATH="/$PROJECT_NAME/settings/local.py"

# Install essential packages from Apt
apt-get update -y
# Python dev packages
apt-get install -y build-essential python python3-dev python3-pip
# Git (we'd rather avoid people keeping credentials for git commits in the repo, but sometimes we need it for pip requirements that aren't in PyPI)
apt-get install -y git

# virtualenv global setup
if [[ ! -f /usr/local/bin/virtualenv ]]; then
    pip3 install virtualenv
fi

# ---

# virtualenv setup for project
su - vagrant -c "/usr/local/bin/virtualenv $VIRTUALENV_DIR --python=/usr/bin/python3.8 && \
    echo $PROJECT_DIR > $VIRTUALENV_DIR/.project && \
    $VIRTUALENV_DIR/bin/pip install -r $PROJECT_DIR/requirements.txt"

# Set execute permissions on manage.py, as they get lost if we build from a zip file
chmod a+x $PROJECT_DIR/manage.py

# Django project setup
su - vagrant -c "source $VIRTUALENV_DIR/bin/activate && cd $PROJECT_DIR && ./manage.py migrate && ./manage.py load_geonames && ./manage.py load_asciified_geonames"
