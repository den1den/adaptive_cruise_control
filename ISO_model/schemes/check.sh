#!/usr/bin/env bash

# https://www.npmjs.com/package/pajv
# pajv -s interpretation_scheme.json -d ../interpretation.yaml

cd ~/Dropbox/0cn
. venv/bin/activate
export PYTHONPATH=.

function _check {
    pajv -s $1 -d $2 --verbose
    # --errors=js --all-errors
}

# Compile all schemes again
for scheme_source in ISO_model/schemes/*_scheme.py
do
    type=$(basename ${scheme_source%_*})
    scheme=ISO_model/generated/${type}_scheme.json
    python ${scheme_source} > ${scheme}
done

_check ISO_model/generated/interpretation_scheme.json ISO_model/interpretation.yaml
_check ISO_model/generated/simple_model_inst_list_scheme.json ISO_model/work_products.json
_check ISO_model/generated/simple_model_inst_list_scheme.json ISO_model/clauses.json
