import json
import sys

import os
import yaml
from jsonschema.validators import validate as json_scheme_validate

from ISO_model.scripts.generators.evl_generator import InterpretationEVLGenerator
from ISO_model.scripts.parsers.emf_model_parser import EmfModelParser
from ISO_model.scripts.parsers.iso_text_parser import IsoTextParser
from ISO_model.scripts.parsers.parser import Parser


DEFAULT_REQUIREMENT_FILES = [
    '/home/dennis/Dropbox/0cn/ISO_model/part1-text.2.txt',
    '/home/dennis/Dropbox/0cn/ISO_model/part3-text.2.txt',
    '/home/dennis/Dropbox/0cn/ISO_model/part4-text.2.txt',
]


class InterpretationParser(Parser):
    def __init__(self) -> None:
        self.emf_model = EmfModelParser()
        self.requirements_model = IsoTextParser()
        self.source = {}
        self.interpretation = {'requirements': {}}
        self.model_refs = {}
        self.exit_code = 0

    def load(self, file_name=None):
        if file_name is None:
            file_name = r'/home/dennis/Dropbox/0cn/ISO_model/interpretation.yaml'
        if file_name.endswith('.yaml'):
            self.source.update(yaml.safe_load(open(file_name)))
        else:
            self.source.update(json.load(open(file_name)))

        # load context
        for model_file in self.get_context('model_files'):
            self.emf_model.load(model_file)
        for req_file in self.get_context('requirement_files', DEFAULT_REQUIREMENT_FILES):
            self.requirements_model.load(req_file)

    def validate(self):
        from ISO_model.scripts.schemes.interpretation_scheme import InterpretationScheme
        json_scheme_validate(self.source, InterpretationScheme().get_schema())

    def validate_normalized(self):
        # check if the normalized document is valid as well
        from ISO_model.scripts.schemes.interpretation_scheme import InterpretationScheme
        json_scheme_validate(self.interpretation, InterpretationScheme().get_schema())

    def normalize(self):
        for req_id, req_obj in self.interpretation['requirements'].items():
            # Normalize ocl notation
            for ocl_level, ocl_roots in req_obj.setdefault('ocl', {}).items():
                for ocl in ocl_roots:
                    ocl.setdefault('pre', [])
                    ocl.setdefault('post', [])
                    if 't' in ocl:
                        # Replace t <- ts
                        ocl['ts'] = [{
                            't': ocl['t'],
                            'messages': '"%s"' % self.requirements_model.output.get(req_id, 'Requirement not in JSON')
                        }]
                        del ocl['t']
                    elif 'ts' in ocl:
                        # Replace ts strings by dicts
                        ocl['ts'] = [
                            {'t': t} if type(t) is str else
                            t for t in ocl['ts']
                        ]
                    else:
                        ocl['ts'] = []
                    self._parser_ocl(ocl)

            # Store all model references
            for model_ref in req_obj.get('pr_model', []):
                self.model_refs.setdefault(model_ref, []).append(req_id)

    def dump_normalized(self):
        json.dump(self.interpretation, open(self.get_context('normalized_output_file'), 'w+'))

    def get_context(self, context_param, default=None):
        v = self.source['context'].get(context_param)
        if v is None:
            if default is None:
                raise Exception("context.%s not set" % context_param)
            else:
                return default
        return v

    def parse(self):
        self.emf_model.parse()
        self.requirements_model.parse()
        # Fill all requirements
        for key, vals in self.source.items():
            if key.startswith('requirement'):
                # assert no duplicate requirement ids
                assert len([dup for dup in vals.keys() if dup in self.interpretation['requirements']]) == 0
                self.interpretation['requirements'].update(vals)

    def _parser_ocl(self, ocl):
        # Look for keywords
        item_class = ocl['c']
        for ocl_test in ocl['ts']:
            txt = ocl_test['t']
            m = InterpretationEVLGenerator.re_possible_att.match(txt)
            if m:
                item_attribute = m.group(1)
                # Check against model
                ac = self.emf_model.has_att(item_class, item_attribute)
                if not ac:
                    raise AssertionError(
                        "Attribute %s not found in %s, off %s" % (item_attribute, item_class, txt))
                if not self.emf_model.class_is_subclass_of(ac, 'Check'):
                    raise AssertionError(
                        "Expected sub-class of Check, but got %s in %s" % (ac, txt))
                # Interpret check attribute keyword
                check_class = ac
                # Generate pre
                create_missing_evl = (
                        'for (x : {item_class} in {item_class}.all().select(x|x.{item_attribute}.isUndefined()) ) {{' +
                        ' x.{item_attribute} = new {check_class}; ' +
                        '}}'
                ).format(item_class=item_class, item_attribute=item_attribute, check_class=check_class)
                ocl['pre'] += [
                    '// CREATE ' + item_class + '.' + item_attribute,
                    create_missing_evl,
                    '//'
                ]
                # Overwrite check
                ocl_test['t'] = (
                    'self.{item_attribute}.checked'
                ).format(item_attribute=item_attribute)


def main():
    if len(sys.argv) > 1:
        inter = InterpretationParser()
        inter.load(sys.argv[1])
        inter.validate()
        return

    inter = InterpretationParser()
    inter.load('ISO_model/interpretation_test.yaml')
    inter.validate()
    inter.parse()
    inter.normalize()
    inter.validate_normalized()
    for ref, req_id in sorted(inter.model_refs.items()):
        print('%s: %s' % (ref, req_id))


if __name__ == '__main__':
    main()
