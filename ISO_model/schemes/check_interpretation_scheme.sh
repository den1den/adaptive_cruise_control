#!/usr/bin/env bash
. venv/bin/activate
export PYTHONPATH=.

# rebuild the interpretation scheme
python ISO_model/schemes/interpretation_scheme.py || exit -1

# Check using command line `pajv`
# with custom filtering
set -o pipefail
echo
pajv -s "ISO_model/generated/interpretation_scheme.json" -d $1 --verbose --errors=text --all-errors 2>&1 \
| sed 's/,\s/\n/g' | sed 's/should NOT have additional properties/Has a wrong key/g' \
&& python ISO_model/scripts/generate_EVL.py $1 || exit -1
