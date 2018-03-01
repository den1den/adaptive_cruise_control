#!/usr/bin/env bash

# Creates interpretation JSON scheme
# Tests with `pajv` command
cd /home/dennis/Dropbox/0cn
. venv/bin/activate
export PYTHONPATH=.
set -o pipefail

filename=$(basename $1)
filename=${filename%.*}
requirement_scheme=generated/schemes/normal_requirement_spec_scheme.json
requirement_strict_scheme=generated/schemes/normal_requirement_strict_scheme.json

echo "# building the requirement schemes"
python scripts/schemes/uc_safety_requirement.py || exit 1
echo "# check against requirement scheme"
scripts/dev/pajv.sh -s ${requirement_scheme} -d $1 || exit 2

echo "# interpret to json"
python scripts/parsers/requirement_parser.py $1 generated/${filename}.json || exit 3
echo "# strict validation on json"
scripts/dev/pajv.sh -s ${requirement_strict_scheme} -d generated/${filename}.json || exit 4

echo "# create full requirement md file"
python scripts/parsers/requirement_parser.py \
acc_project/requirements/functional_requirements.yaml \
acc_project/requirements/law_requirements.yaml \
acc_project/requirements/non_functional_requirements.yaml \
generated/project_requirements.json generated/project/project_requirements.md  || exit 5
