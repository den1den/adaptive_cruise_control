import json

def has_model_reference(req_interpetation, model_ref):
    if 'pr_model' not in req_interpetation:
        return False
    for val in req_interpetation['pr_model']:
        if type(val) is str:
            if val == model_ref:
                return True
        else:
            val = val['pr_model']
            if val == model_ref:
                return True
    return False

# att = input('Give an attribute or class: (Class.attr)\n')
att = 'PKSRDerivation'

inter = json.load(open('ISO_model/interpretation.json'))
reqs = inter['requirements']

atts = att.split('.')
atts = ['.'.join(atts[:i]) for i in range(len(atts), 0, -1)]

has_match = False
i = 1
for att in atts:
    matches = []
    for req_id, req_i in reqs.items():
        if has_model_reference(req_i, att):
            has_match = True
            matches += [req_id]
    if len(matches) > 0:
        print("%s match: %s" % (i, matches, ))
    i += 1

if not has_match:
    print("No match found")