import json
import re

import sys
from jsonschema import validate as json_scheme_validate

from ISO_model.schemes.simple_model_inst_list_scheme import ModelInstanceIdList


def class_name_to_hutn_prefix(class_name):
    cln_capitals = ''.join(filter(str.isupper, class_name))
    if len(cln_capitals) >= 2:
        return cln_capitals.lower()
    else:
        return class_name[:2].lower()


class HutnGenerator:

    def __init__(self, outfile) -> None:
        self.out = open(outfile, 'w+')
        self.indent = 0
        self.instances = {}

    def _finish(self):
        for i in range(self.indent):
            self.close_block()
        self.out.close()

    def print_block(self, title, fn=None):
        self._print(title + ' {', 1)
        if fn:
            fn()
            self.close_block()

    def inst(self, class_name, hutn_id, obj=None, keys=None):
        if obj is None:
            obj = {}
        self.print_block('%s "%s"' % (class_name, hutn_id), lambda: self.values(obj, keys))

    def inst_with_id(self, class_name, obj, keys=None):
        hutn_id_prefix = class_name_to_hutn_prefix(class_name)
        self.inst(class_name, hutn_id_prefix + obj['id'], obj, keys)

    def values(self, key_values, keys=None):
        if not keys:
            keys = sorted(key_values.keys())
        for k in keys:
            if k.endswith('__refs_to_id'):
                continue
            reference_to = key_values.get(k + '__refs_to_id', None)
            v = key_values[k]
            self.print_kv(k, v, reference_to)

    def print_kv(self, key, value, reference_to=None):
        if type(key) is not str:
            raise AssertionError("Key must be string of `%s`" % key)
        self._print(key + ': ' + self.to_repr(value, reference_to))

    def close_block(self):
        self.indent -= 1
        self._print('}')

    def _print(self, line=None, indent_inc=0):
        if line:
            print('\t' * self.indent + line, file=self.out)
        else:
            print(file=self.out)
        self.indent += indent_inc

    def to_repr(self, value, reference_to=None):
        if type(value) is list:
            value_strings = [self.to_repr(v, reference_to) for v in value]
            if reference_to:
                return ', '.join(value_strings)
            else:
                return "[" + ', '.join(value_strings) + "]"
        if reference_to:
            ref_id_prefix = class_name_to_hutn_prefix(reference_to)
            return reference_to + ' "' + ref_id_prefix + value + '"'
        if type(value) is str:
            return '"' + value + '"'
        elif type(value) is int:
            return "%d" % value
        raise AssertionError("value type `%s` not recognized for `%s`" % (type(value), value))

    def print_model_instances(self, filename):
        # filename must adhere to `model_inst_list` scheme
        root = json.load(open(filename))
        json_scheme_validate(root, ModelInstanceIdList.get_schema())
        class_name = root['class_name']
        instances_dict = root['instances']
        for inst_id, instance_data in sorted(instances_dict.items()):
            instance_data.setdefault('id', inst_id)
            self.inst_with_id(class_name, instance_data)


class IsoModelHutnGenerator(HutnGenerator):
    def __init__(self, outfile) -> None:
        super(IsoModelHutnGenerator, self).__init__(outfile)
        self.requirements = {}
        # self.out = sys.stdout

    def load_requirements(self, *files):
        for file in files:
            self.requirements.update(json.load(open(file)))

    def generate_iso(self, work_products_file):
        self._print('@Spec { metamodel "iso_research" { nsUri: "iso_research" } }')
        self._print()

        package = 'project_model'
        package = 'iso_model'
        self._print(package + ' {', 1)

        # Requirements
        for r_id, r in sorted(self.requirements.items()):
            if any((r['annotations'].get(a, False) for a
                    in ('ignore', 'work_product'))):
                continue
            r['name'] = r['title']
            r.setdefault('id', r_id)
            self.inst_with_id('IsoRequirement', r, ('id', 'name'))

        self.print_model_instances('../clauses.json')
        self.print_model_instances(work_products_file)

        self._finish()


if __name__ == '__main__':
    g = IsoModelHutnGenerator('../../acc_mm/model/iso/iso_model/generated/iso26262.hutn')
    g.load_requirements('../generated/part3-text.2.json',)
    g.generate_iso('../generated/work_products.json')
