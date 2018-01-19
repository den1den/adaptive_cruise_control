#!/usr/bin/env bash

# Creates interpretation JSON scheme
# Tests with `pajv` command
# Generates EVL file

. venv/bin/activate
export PYTHONPATH=.

# rebuild the interpretation scheme
python ISO_model/scripts/schemes/interpretation_scheme.py || exit -1

# with custom filtering
set -o pipefail
echo
pajv -s "ISO_model/generated/interpretation_scheme.json" -d $1 --verbose --errors=text --all-errors 2>&1 \
| sed 's/,\s/\n/g' | sed 's/should NOT have additional properties/Has a wrong key/g' \
&& python ISO_model/scripts/generators/evl_generator.py $1 || exit -1
