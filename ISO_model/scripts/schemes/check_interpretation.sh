#!/usr/bin/env bash

# Creates interpretation JSON scheme
# Tests with `pajv` command
# Generates EVL file

. venv/bin/activate
export PYTHONPATH=.
set -o pipefail

filename=$(basename $1)
filename=${filename%.*}
context_scheme=ISO_model/generated/context_scheme.json
interpretation_scheme=ISO_model/generated/${filename}_scheme.json

echo "# building the context scheme"
python ISO_model/scripts/schemes/context_scheme.py ${context_scheme} || exit 1
echo "# check against context scheme"
ISO_model/scripts/schemes/pajv.sh -s ${context_scheme} -d $1 || exit 2

echo "# build the interpretation scheme"
python ISO_model/scripts/schemes/interpretation_scheme.py $1 ${interpretation_scheme} || exit 3

echo "# check against interpretation scheme"
ISO_model/scripts/schemes/pajv.sh -s ${interpretation_scheme} -d $1 || exit 4

echo "# parse the interpretation file to json"
python ISO_model/scripts/parsers/interpretation_parser.py $1 || exit 4

echo "# build the EVL file"
python ISO_model/scripts/generators/evl_generator.py $1 || exit 5
