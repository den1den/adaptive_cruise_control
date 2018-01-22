#!/usr/bin/env bash

# Creates interpretation JSON scheme
# Tests with `pajv` command
# Generates EVL file

. venv/bin/activate
export PYTHONPATH=.
set -o pipefail

filename=$(basename $1)
filename=${filename%.*}

# build the context scheme
python ISO_model/scripts/schemes/context_scheme.py || exit 1
# check against context scheme
ISO_model/scripts/schemes/pajv.sh -s "ISO_model/generated/context_scheme.json" -d $1 --verbose --errors=text --all-errors || exit 2

# build the interpretation scheme
scheme=ISO_model/generated/${filename}_scheme.json
python ISO_model/scripts/schemes/interpretation_scheme.py $1 ${scheme} || exit 3

# check against interpretation scheme
echo
ISO_model/scripts/schemes/pajv.sh -s ${scheme} -d $1 --verbose --errors=text --all-errors || exit 4

# write the json file
python ISO_model/scripts/parsers/interpretation_parser.py $1 || exit 4

# build the EVL file
python ISO_model/scripts/generators/evl_generator.py $1 || exit 5
