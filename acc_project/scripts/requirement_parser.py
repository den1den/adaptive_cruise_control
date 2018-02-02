import json
import os
import sys

import yaml
from jsonschema import validate

from ISO_model.scripts.generators.md_generator import MdGenerator
from ISO_model.scripts.lib.util import dict_poll_update, dict_update, dict_set_default
from ISO_model.scripts.parsers.parser import Parser
from ISO_model.scripts.schemes.project_model.safety_requirement_scheme import RequirementsSpecFile, \
    NormalRequirementSpec, RequirementsListFile, NormalRequirementStrict
from acc_project.scripts.asil import Asil

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


class ProjectRequirementParser(Parser):

    def __init__(self) -> None:
        self.input = []
        self.requirements = {}
        self.errors = []

    def load(self, file_name):
        self.input.append((file_name, yaml.safe_load(open(file_name))))

    def validate(self):
        s = RequirementsSpecFile(NormalRequirementSpec).get_schema()
        for file_name, d in self.input:
            validate(d, s)

    def validate_output(self):
        s = RequirementsListFile(NormalRequirementStrict).get_schema()
        validate({'requirements': self.requirements}, s)

    def parse(self):
        for file_name, d in self.input:
            self._parse_reqs(d['requirements'], {
                'allocated_to': [],
                'notation': 'informal',
                'requirement_type': d['requirements_type'],
                'requirement_file': file_name,
            })
            self.validate_output()

    def _parse_reqs(self, d: dict, defaults=None, parent=None):
        if defaults is None:
            defaults = {}
        defaults = dict_poll_update(d, 'default', defaults)
        for req_id, req in d.items():
            dict_set_default(req, defaults)

            req['req_id'] = req_id
            if type(req['allocated_to']) is not list:
                req['allocated_to'] = [req['allocated_to'], ]

            if parent:
                req.setdefault('parent', parent['req_id'])

            if req_id in self.requirements:
                raise AssertionError("requirement id %s is duplicate" % req_id)
            self.requirements[req_id] = req

            if 'children' in req:
                children = req.pop('children')
                if type(children) is dict:
                    children = [children]
                for child_group in children:
                    children_defaults = defaults.copy()
                    children_defaults['allocated_to'] = req['allocated_to']
                    self._parse_reqs(child_group, children_defaults, req)

    def to_json(self, file_name):
        return json.dump({
            'requirements': self.requirements
        }, open(file_name, 'w+'), indent=2)

    def to_md(self, filename):
        md = MdGenerator(open(filename, 'w+'))
        TABLE_HEADING = ('requirement_type', 'notation', 'req_class', 'allocated_to')

        rs = self.requirements.copy()
        while len(rs) > 0:
            nxt = sorted(rs)[0]
            r = rs[nxt]
            md.h(r['req_id'])
            md.p(r['description'])
            md.single_table(r, TABLE_HEADING)
            md.open_quote()
            for ps in sorted(rs)[1:]:
                child_req = rs[ps]
                if child_req.get('parent') == r['req_id']:
                    md.h(child_req['req_id'], 2)
                    md.p(child_req['description'])
                    md.single_table(child_req, TABLE_HEADING)
                    del rs[ps]
            del rs[nxt]
            md.close_quote()


        md.close()


    def log_error(self, msg, req_dict, *params):
        self.errors.append("%s\n\tat %s" % (msg % params, req_dict,))


if __name__ == '__main__':
    p = ProjectRequirementParser()
    p.load('/home/dennis/Dropbox/0cn/acc_project/requirements/functional_requirements.yaml')
    p.parse()
    p.to_json('/home/dennis/Dropbox/0cn/generated/requirements.json')
    p.to_md('/home/dennis/Dropbox/0cn/generated/requirements.md')


def print_errors(errors):
    sys.stdout.flush()
    for err in errors:
        print(err, file=sys.stderr)
    sys.stderr.flush()
