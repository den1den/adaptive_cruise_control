import json
import os
import sys

import yaml
from ruamel.yaml import YAML
from ruamel.yaml.constructor import SafeConstructor
from yaml.parser import ParserError

from acc_project.scripts.asil import Asil
from acc_project.scripts.requirement import Requirement

requirement_types = yaml.safe_load(open(
    os.path.join(os.path.dirname(__file__), '../aux_definitions/requirement_types.yaml')
))


def pop(dic: dict, key: str, default=None):
    if key in dic:
        val = dic.pop(key)
        if val is None:
            return default
        return val
    else:
        return default


class ProjectRequirementParser:

    def __init__(self) -> None:
        self.output = {}
        self.errors = []
        self.required_keys = (
            'id',
            'requirement_type',
            'text',
            'assigned_to',
            'level',
        )
        self.filename = None

    def parse(self, yaml_filename: str):
        with open(yaml_filename) as f:
            try:
                yaml_parser = YAML(typ='safe')
                obj = yaml_parser.load(f)
            except Exception as e:
                self.errors.append("%s\nCould not parse %s" % (e, yaml_filename, ))
                return
        self.filename = yaml_filename
        for req_type, reqs in obj.items():
            if reqs is None:
                self.errors.append("Empty requirements key `%s` in `%s`" % (req_type, yaml_filename))
                continue
            defaults = {'requirement_type': req_type}
            self._parse_reqs(reqs, defaults)

    def _parse_reqs(self, reqs: dict, defaults: dict):
        defaults = self.set_default(
            pop(reqs, 'default', {}),
            defaults
        )
        for req_id, req in reqs.items():
            if req is None:
                continue
            req['id'] = req_id
            self._parse_req(req, defaults)

    def _parse_req(self, req_dict: dict, defaults: dict):
        # id
        rid = req_dict['id']
        if rid in self.output:
            self.log_error('Duplicate id `%s`', req_dict,
                           rid)
            return
        #
        # Check parsing of a single ID
        #
        if rid == 'SR3.2.1':
            k = 0

        req_dict = self.set_default(req_dict, defaults)

        # check missing keys
        for key in self.required_keys:
            if key not in req_dict:
                self.log_error('Missing key `%s`', req_dict,
                               key)
                return

        # requirement_type
        r_type = req_dict['requirement_type']
        if r_type.startswith('dummy_'):
            return
        valid_r_type = None
        for t in requirement_types:
            if r_type.startswith(t):
                valid_r_type = t
        if valid_r_type is None:
            self.log_error('Could not deduce requirement type `%s` out of %s', req_dict,
                           r_type, requirement_types)
            return
        req_dict['requirement_type'] = valid_r_type
        req_dict['original_requirement_type'] = r_type

        req = Requirement(req_dict, self.filename)
        self.output[rid] = req

        # children
        children = pop(req_dict, 'children_requirements', {})
        self._parse_reqs(children, self.set_default(
            {'requirement_parent': rid},
            defaults
        ))

    def set_default(self, original, defaults):
        for key, default_value in defaults.items():
            is_addition = ('+' + key) in original
            if is_addition:
                original_value = original.pop('+' + key)
                original[key] = default_value + original_value
            else:
                original.setdefault(key, default_value)
        return original

    def to_json(self):
        out = [r.requirement for r in self.output.values()]
        return json.dumps(out, cls=Asil.JsonEncoder, indent=2)

    def log_error(self, msg, req_dict, *params):
        self.errors.append("%s\n\tat %s" % (msg % params, req_dict,))


if __name__ == '__main__':
    # test
    p = ProjectRequirementParser()
    # p.parse('../requirements/obstacle_detector_requirements.yaml')
    p.parse('../requirements/functional_requirements.yaml')
    print(p.to_json())


def print_errors(errors):
    sys.stdout.flush()
    for err in errors:
        print(err, file=sys.stderr)
    sys.stderr.flush()
