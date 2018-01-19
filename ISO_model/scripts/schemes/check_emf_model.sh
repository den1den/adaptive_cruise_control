#!/usr/bin/env bash

# Parses an EOL file with python

. venv/bin/activate
export PYTHONPATH=.

python ISO_model/scripts/parsers/emf_model_parser.py $1 || exit -1
