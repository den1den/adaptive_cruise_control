#!/usr/bin/env bash

# Parses an EOL file with python

. venv/bin/activate
export PYTHONPATH=.

python ISO_model/scripts/extract_emfatic.py $1 || exit -1
