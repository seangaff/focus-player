#! /bin/bash

PROJECT_NAME="focus-player"
PYTHON_VERSION="3.13.7"

# Create virtualenv
if ! pyenv version | grep -q $PROJECT_NAME; then
    echo "Creating virtual env: $PROJECT_NAME"
    pyenv install  $PYTHON_VERSION
    pyenv virtualenv $PYTHON_VERSION $PROJECT_NAME
fi

#  Activate virtualenv
pyenv local $PROJECT_NAME

# Install deps
pip install -r requirements.txt