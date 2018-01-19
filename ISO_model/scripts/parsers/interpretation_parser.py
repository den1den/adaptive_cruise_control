import json
import sys

import yaml
from jsonschema.validators import validate as json_scheme_validate

from ISO_model.scripts.generators.evl_generator import InterpretationEVLGenerator
from ISO_model.scripts.parsers.emf_model_parser import EmfModelParser
from ISO_model.scripts.parsers.parser import Parser


class InterpretationParser(Parser):
    def __init__(self) -> None:
        self.emf_model = None
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

    def validate(self):
        from ISO_model.scripts.schemes.interpretation_scheme import InterpretationDocument
        json_scheme_validate(self.source, InterpretationDocument().get_schema())

    def normalize(self, emf_model=None, normalize_out_file=None):
        from ISO_model.scripts.schemes.interpretation_scheme import InterpretationDocument
        self.emf_model = emf_model or self.emf_model
        if self.emf_model is None:
            self.emf_model = EmfModelParser()
            self.emf_model.load()
            self.emf_model.parse()

        for req_id, req_obj in self.interpretation['requirements'].items():
            # Normalize ocl notation
            for ocl_level, ocl_roots in req_obj.setdefault('ocl', {}).items():
                for ocl in ocl_roots:
                    ocl.setdefault('pre', [])
                    if 't' in ocl:
                        # Replace t <- ts
                        ocl['ts'] = [
                            {'t': ocl['t']}
                        ]
                        del ocl['t']
                    else:
                        # Replace ts strings by dicts
                        ocl['ts'] = [
                            {'t': t} if type(t) is str else
                            t for t in ocl['ts']
                        ]
                    self._parser_ocl(ocl)

            # Store all model references
            for model_ref in req_obj.get('pr_model', []):
                self.model_refs.setdefault(model_ref, []).append(req_id)

        if normalize_out_file:
            json.dump(self.interpretation, open(normalize_out_file, 'w+'))

        # check if the normalized document is valid as well
        try:
            json_scheme_validate(self.interpretation, InterpretationDocument().get_schema())
        except Exception as e:
            if normalize_out_file:
                print('Run: pajv -s "ISO_model/generated/interpretation_scheme.json" -d %s'
                      ' --verbose --errors=text --all-errors' % normalize_out_file)
                exit(-1)
            else:
                raise e

    def parse(self):
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

    emf_model = EmfModelParser()
    emf_model.load()
    emf_model.parse()

    inter = InterpretationParser()
    inter.load('ISO_model/interpretation_test.yaml')
    inter.parse()
    inter.normalize(emf_model)
    for ref, req_id in sorted(inter.model_refs.items()):
        print('%s: %s' % (ref, req_id))


if __name__ == '__main__':
    main()
