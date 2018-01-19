import json
import re

import yaml
from jsonschema.validators import validate as json_scheme_validate


class InterpretationParser:
    def __init__(self) -> None:
        self.interpretation = {'requirements': {}}
        self.model_refs = {}

    def check_interpretation_yaml(self, filename=None):
        from ISO_model.schemes.interpretation_scheme import InterpretationDocument
        if filename is None:
            filename = '/home/dennis/Dropbox/0cn/ISO_model/ip.yaml'
        i = yaml.safe_load(open(filename))
        json_scheme_validate(i, InterpretationDocument().get_schema())

    def load_interpretation_yaml(self, filename=None):
        if filename is None:
            filename = r'/home/dennis/Dropbox/0cn/ISO_model/interpretation.yaml'
        self._parse(yaml.safe_load(open(filename)))

    def _parse(self, interpretation_obj):
        # silent overwrite
        for key, vals in interpretation_obj.items():
            if key.startswith('requirement'):
                self.interpretation['requirements'].update(vals)
        for req_id, req_obj in self.interpretation['requirements'].items():
            for model_ref in req_obj.get('pr_model', []):
                self.model_refs.setdefault(model_ref, []).append(req_id)


if __name__ == '__main__':
    ip = InterpretationParser()
    ip.load_interpretation_yaml()

    for ref, req_id in sorted(ip.model_refs.items()):
        print('%s: %s' % (ref, req_id))
