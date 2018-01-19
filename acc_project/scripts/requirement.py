import os
import yaml

from acc_project.scripts.asil import Asil

external_systems = yaml.safe_load(open(
    os.path.join(os.path.dirname(__file__), '../aux_definitions/external_systems.yaml')
))


class Requirement:
    """
    A requirement (with its dependency tree)
    """

    def __init__(self, requirement_dict, filename):
        # requirement_parent
        ps = requirement_dict.setdefault('requirement_parent', ())
        if type(ps) is str:
            requirement_dict['requirement_parent'] = (ps,)
        # asil
        asil = requirement_dict.get('asil')
        if asil is not None:
            requirement_dict['asil'] = Asil(asil)
        self.requirement = requirement_dict
        self.parents = []
        self.children = []

        self.location = filename

    def id(self):
        return self.requirement['id']

    def add_parent(self, parent):
        self.parents.append(parent)
        parent.children.append(self)

    def get_sg_parent_ids(self):
        return [p for p in self.requirement['requirement_parent'] if p.startswith('SG')]

    def get_req_parent_ids(self):
        return [p for p in self.requirement['requirement_parent'] if not p.startswith('SG')]

    def get_roots(self, roots=None):
        if roots is None:
            roots = set()
        if len(self.parents) == 0:
            roots |= {self}
        for p in self.parents:
            p.get_roots(roots)
        return roots

    def __repr__(self):
        if self.location:
            return "%s \"%s\"" % (self.requirement['id'], self.location,)
        else:
            return "%s" % (self.requirement['id'],)

    def is_of_external(self):
        for ext_level, ext_assigned_to in external_systems:
            if self.requirement['level'] == ext_level and \
                    self.requirement['assigned_to'] == ext_assigned_to:
                return True
        return False

    def is_safety_req(self):
        return self.requirement['requirement_type'] == 'safety_requirement'


def make_dep_tree(all_requirements_map):
    for req in all_requirements_map.values():
        parents = req.get_req_parent_ids()
        for parent_id in parents:
            parent = all_requirements_map.get(parent_id)
            if parent is None:
                raise Exception("Missing parent id %s" % req)
            req.add_parent(parent)
    return [root for root in all_requirements_map.values() if len(root.parents) == 0]
