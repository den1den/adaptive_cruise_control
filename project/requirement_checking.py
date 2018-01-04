import json
import os
import sys

import yaml

from project.safety_goals_checking import get_safety_goals
from project.scripts.asil import Asil
from project.scripts.requirement import make_dep_tree, Requirement
from project.scripts.requirement_parser import RequirementParser, print_errors
from scripts.dot_template_renderer import yaml_and_template_to_dot, template_to_dot, template_to_png

value_classes = yaml.safe_load(open(
    os.path.join(os.path.dirname(__file__), 'aux_definitions/classes.yaml')
))


class Checker:
    """
    Checks and fill in extra values of the Requirements
    """

    def __init__(self):
        self.req_roots = []
        self.reqs = {}
        self.errors = []
        self.safety_goals = get_safety_goals()
        self.parser = RequirementParser()
        self.references_used = {}
        self.values_used = {}

    def load_yaml(self, yaml_filename):
        l0 = len(self.parser.errors)
        self.parser.parse(yaml_filename)
        success = len(self.parser.errors) == l0
        if success:
            print("Loaded in %s" % yaml_filename)
        return success

    def run(self):
        if len(self.parser.errors) > 0:
            print_errors(self.parser.errors)
            return False
        self.reqs = self.parser.output
        self.usage_check()
        self.simple_check()
        if self.check_parents():
            self.req_roots = make_dep_tree(self.reqs)
            self.tree_check()
        self.print_errors()
        return True

    def usage_check(self):
        for r in self.reqs.values():
            # Fill self.references_used
            # from `assigned_to` and `level`
            r_assigned_to = r.requirement['assigned_to']
            r_level = r.requirement['level']
            r_values_used = r.requirement.get('values_used', [])
            self.references_used.setdefault(r_assigned_to, {}) \
                .setdefault(r_level, []) \
                .append(r)

            # Add self.references_used
            # from `references_used` key as well
            n_level = None
            for ref_dict in r.requirement.get('references_used', []):
                n = ref_dict['name']
                n_level = ref_dict.get('level', n_level)
                if n_level is None:
                    self.log_error("Missing level in `%s`", r,
                                   ref_dict)
                elif n_level != r_level and n != r_assigned_to:
                    self.references_used.setdefault(n, {}) \
                        .setdefault(n_level, []) \
                        .append(r)

            # Fill self.values_used
            v_type = None
            for value_dict in r_values_used:
                v = value_dict.get('value')
                v_type = value_dict.get('type', v_type)
                self.check_value(r, v, v_type)

    def check_value(self, r, value: str, v_type):
        if v_type is None:
            self.log_error("Missing `type` in the `values_used`", r)
            return
        if value is None:
            # self.log_error("Missing `value` in the `values_used`", r)
            # Missing value is OK, to set only the type
            return
        value = str(value)
        self.values_used.setdefault(v_type, {}) \
            .setdefault(value, []) \
            .append(r)
        if value not in r.requirement['text']:
            self.log_error("Used value `%s` missing in text `%s`", r,
                           value, r.requirement['text'])
        if v_type not in value_classes:
            self.log_error("Type `%s` is not defined in `%s`", r,
                           v_type, value_classes.keys())
            return

        class_spec = value_classes.get(v_type) or {}
        if class_spec.get('super', '').lower() in ('real', 'float', 'cecimal'):
            if not value.isdecimal():
                return self.log_error("Value should be digit, instead of `%s`", r, value)
        if class_spec.get('super', '').lower() in ('int', 'integer', 'number'):
            if not value.isdigit():
                return self.log_error("Value should be digit, instead of `%s`", r, value)
        if 'values' in class_spec:
            if value not in class_spec['values']:
                return self.log_error("Not allowed value `%s`, should be one of `%s`", r, value, class_spec['values'])

    def tree_check(self):
        for root in self.req_roots:
            self._tree_check(root)

    def _tree_check(self, root, min_asil=None):
        min_asil = self._tree_asil_check(min_asil, root)
        if len(root.children) == 0:
            self._tree_leaf_check(root)

        for child in root.children:
            self._tree_check(child, min_asil)

    def _tree_asil_check(self, min_asil, root):
        has_parent_asil = min_asil is not None
        for sg_id in root.get_sg_parent_ids():
            sg = self.safety_goals[sg_id]
            sg_asil = sg['asil']
            if min_asil is None or sg_asil > min_asil:
                min_asil = sg_asil
        asil = root.requirement.get('asil')
        if min_asil is None:
            # No asil to check
            min_asil = asil
        elif asil is None:
            # Missing asil value
            if not has_parent_asil:
                self.log_error("missing asil value, while parent is missing as well", root)
            else:
                # Update with minimum asil
                root.requirement['asil'] = min_asil
        else:
            # Check asil value
            if asil < min_asil:
                self.log_error("asil is too low. asil is `%s` minimum asil is `%s`", root,
                               asil, min_asil)
        return min_asil

    def check_parents(self):
        success = True
        for req in self.reqs.values():
            for parent in req.get_req_parent_ids():
                if parent not in self.reqs:
                    self.log_error("could not find parent %s", req,
                                   parent)
                    success = False
        return success

    def _tree_leaf_check(self, leaf: Requirement):
        # Do not check external systems
        if leaf.is_of_external():
            return
        # Only check safety requirements
        if not leaf.is_safety_req():
            return

        # Check internal systems
        leaf_levels = (
            'sw_unit',
            'hw_unit',
        )
        if leaf.requirement['level'] not in leaf_levels:
            self.log_error("is a leaf but level `%s` and is not in %s. root is `%s`", leaf,
                           leaf.requirement['level'], leaf_levels, leaf.get_roots())

    def get_req_dicts(self):
        return [r.requirement for r in self.reqs.values()]

    def simple_check(self):
        for r in self.reqs.values():
            txt = r.requirement.get('text')
            if txt is None or txt == '':
                self.log_error("missing text", r)

    def print_req(self, id):
        r = self.reqs.get(id)
        if r is None:
            print("Requirement `%s` could not be found" % id)
        print("Requirement `%s`=\n%s" % (id, r.requirement))

    def log_error(self, msg: str, r: Requirement, *params):
        self.errors.append((msg, r, params, ))

    def print_errors(self):
        print_errors((
            "%s: %s" % (r.id(), msg % params) for (msg, r, params) in sorted(self.errors, key=lambda e: e[1].id())
        ))


def flatten_2d_req_map(var):
    return {k1: {k2: [r.id() for r in requirements]
                 for k2, requirements in var2.items()}
            for k1, var2 in var.items()}


def process_srs():
    srs_json = 'project/safety_requirements/srs.json'
    if os.path.exists(srs_json):
        os.remove(srs_json)

    checker = Checker()
    for directory in ('project/safety_requirements', 'project/requirements'):
        for f in os.listdir(directory):
            if f.endswith('.yaml'):
                checker.load_yaml(os.path.join(directory, f))
    if not checker.run():
        print("\nRequirements could not be checked!\n", file=sys.stderr)
        return

    # checker.print_req('ACC_FR_2')

    json.dump(flatten_2d_req_map(checker.references_used), open('project/aux_definitions/out_references_used.json', 'w+'), indent=2)
    json.dump(flatten_2d_req_map(checker.values_used), open('project/aux_definitions/out_values_used.json', 'w+'), indent=2)
    json.dump(checker.get_req_dicts(), open(srs_json, 'w+'), indent=2, cls=Asil.JsonEncoder)

    template_to_png('project/safety_requirements/srs-dependency-graph.template.dot', {'requirements': checker.reqs})

    print("Requirements checked\n")


if __name__ == '__main__':
    process_srs()
