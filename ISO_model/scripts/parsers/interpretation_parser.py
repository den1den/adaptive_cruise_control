import json
import re
import sys

import os
import yaml
from jsonschema.validators import validate as json_scheme_validate
from nltk.chunk import regexp

from ISO_model.scripts.generators.evl_generator import InterpretationEVLGenerator
from ISO_model.scripts.lib.util import dict_poll, dict_val_to_array, dict_poll_all_if_present, dict_remove_if_empty_list
from ISO_model.scripts.parsers.emf_model_parser import EmfModelParser
from ISO_model.scripts.parsers.iso_text_parser import IsoTextParser
from ISO_model.scripts.parsers.parser import Parser


DEFAULT_REQUIREMENT_FILES = [
    '/home/dennis/Dropbox/0cn/ISO_model/text/ISO-1-text.txt',
    '/home/dennis/Dropbox/0cn/ISO_model/text/ISO-3-text.txt',
    '/home/dennis/Dropbox/0cn/ISO_model/text/ISO-4-text.txt',
    '/home/dennis/Dropbox/0cn/ISO_model/text/ISO-8-text.txt',
]
DEFAULT_INTERPRETATION_JSON_FILE = r'/home/dennis/Dropbox/0cn/ISO_model/generated/interpretation.json'


class InterpretationParser(Parser):
    eol_var_name = '[a-z_][a-zA-Z0-9_]*'
    eol_class_name = '[a-zA-Z0-9_]*'
    eol_value = '(?:{cls}\.)?{var}'.format(cls=eol_class_name, var=eol_var_name)
    re_DEFINE = re.compile(r'DEFINE\s+((?:{var}\.)?{var})\s+({value})'.format(var=eol_var_name, value=eol_value))
    re_CREATE = re.compile(r'^CREATE\s+(%s)\s*{([^}]*)}' % eol_class_name)
    re_ASSERT = re.compile(r'ASSERT\s+(.*)\s+MESSAGE\s+(.*)')
    re_CHECK = re.compile(r'^CHECK\s+({var})$'.format(var=eol_var_name))
    re_ASIL = re.compile(r'({val})\s+IS_ASIL_((?:(?:QM)|A|B|C|D|(?:_OR_))+)'.format(val=eol_value))
    code_IF = 'if({cnd}){{{bdy}}}'

    def __init__(self) -> None:
        self.emf_model = EmfModelParser()
        self.iso_req_model = IsoTextParser()
        self.source = {}
        self.interpretation = {'requirements': {}}
        self.model_refs = {}
        self.exit_code = 0
        self._ocl = None
        self._req = None
        self._extra_pre = None

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
            self.iso_req_model.load(req_file)

    def validate(self):
        EmfModelParser.emf_model_for_scheme = self.emf_model
        from ISO_model.scripts.schemes.interpretation_scheme import InterpretationScheme
        json_scheme_validate(self.source, InterpretationScheme().get_schema())

    def validate_normalized(self):
        # check if the normalized document is valid as well
        EmfModelParser.emf_model_for_scheme = self.emf_model
        from ISO_model.scripts.schemes.interpretation_scheme import InterpretationScheme
        json_scheme_validate(self.interpretation, InterpretationScheme().get_schema())

    def normalize(self):
        for req_id, req_obj in self.interpretation['requirements'].items():
            self._req = req_obj

            self._normalize_req(req_id)

            # Store all model references
            for model_ref in req_obj.get('pr_model', []):
                self.model_refs.setdefault(model_ref, []).append(req_id)

            # For testing:
            # try:
            #     self.validate_normalized()
            # except Exception as e:
            #     self._normalize_req(req_id)

        self._req = None
        self._extra_pre = None

    def _normalize_req(self, req_id):
        self._extra_pre = []
        # normalize the requirement object
        dict_val_to_array(self._req, 'pre')
        dict_val_to_array(self._req, 'post')

        self._req['pre'] = self._parse_eol_stmts(self._req['pre'])
        self._req['post'] = self._parse_eol_stmts(self._req['post'])

        # Normalize ocl notation
        for ocl_level, ocl_roots in self._req.get('ocl', {}).items():
            for ocl in ocl_roots:
                self._ocl = ocl
                self._normalize_ocl(req_id)
                self._ocl = None

        self._req['pre'] += self._extra_pre

        # cleanup
        dict_remove_if_empty_list(self._req, 'pre')
        dict_remove_if_empty_list(self._req, 'post')
        self._extra_pre = None

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
        self.iso_req_model.parse()
        # Fill all requirements
        for key, vals in self.source.items():
            if key.startswith('requirement'):
                # assert no duplicate requirement ids
                assert len([dup for dup in vals.keys() if dup in self.interpretation['requirements']]) == 0
                self.interpretation['requirements'].update(vals)

    def _replace_DEFINE(self, m):
        var_name = m.group(1)
        value_name = m.group(2)
        return InterpretationParser.code_IF.format(
            cnd=var_name + '.isUndefined()',
            bdy=var_name + '=' + value_name + ';',
        )

    def _replace_ASIL(self, m):
        value = m.group(1)
        asils = m.group(2).split('_OR_')

        ASILS = {
            'D': ('D', 'D_D'),
            'C': ('C', 'C_C', 'C_D'),
            'B': ('B', 'B_B', 'B_C', 'B_D'),
            'A': ('A', 'A_A', 'A_B', 'A_C', 'A_D'),
            'QM': ('QM', 'QM_A', 'QM_B', 'QM_C', 'QM_D'),
        }
        asils = set((x for asil in asils for x in ASILS[asil]))
        return '/* '+m.group(0)+' */('+' or '.join((value+'='+'ASIL.'+asil for asil in asils))+')'

    def _replace_CREATE(self, m):
        class_name = m.group(1)
        att_values = [att_val.split(':') for att_val in m.group(2).split(',')]
        if len(att_values) == 0:
            return InterpretationParser.code_IF.format(
                cnd=class_name + '.all().length()==0',
                bdy='var x = new ' + class_name + '();',
            )
        else:
            return InterpretationParser.code_IF.format(
                cnd='not ' + class_name + '.all().exists(x|{t})'.format(
                    t=' and '.join(['x.{att}={val}'.format(att=att, val=val) for att, val in att_values]),
                ),
                bdy='var x = new ' + class_name + '(); {c};'.format(
                    c='; '.join(['x.{att}={val}'.format(att=att, val=val) for att, val in att_values]),
                ),
            )

    def _replace_CHECK(self, m):
        item_class = self._ocl['c']
        item_attribute = m.group(1)
        # Check against model
        ac = self.emf_model.has_att(item_class, item_attribute)
        if not ac:
            raise AssertionError(
                "Attribute %s not found in %s, off %s" % (item_attribute, item_class, m))
        if not self.emf_model.class_is_subclass_of(ac, 'Check'):
            raise AssertionError(
                "Expected sub-class of Check, but got %s in %s" % (ac, m))
        # Interpret check attribute keyword
        check_class = ac
        # Generate pre
        create_missing_evl = (
                'for (x : {item_class} in {item_class}.all().select(x|x.{item_attribute}.isUndefined()) ) {{' +
                ' x.{item_attribute} = new {check_class}; ' +
                '}}'
        ).format(item_class=item_class, item_attribute=item_attribute, check_class=check_class)
        self._extra_pre += [
            '// CREATE ' + item_class + '.' + item_attribute,
            create_missing_evl,
        ]
        # Overwrite check
        return 'self.{item_attribute}.checked'.format(item_attribute=item_attribute)

    def _parse_eol_stmts(self, stmts):
        return [self._parse_eol_stmt(s) for s in stmts]

    def _parse_eol_stmt(self, eol):
        eol = self._match_replace(eol, InterpretationParser.re_DEFINE, self._replace_DEFINE)
        eol = self._match_replace(eol, InterpretationParser.re_CREATE, self._replace_CREATE)
        eol = self._match_replace(eol, InterpretationParser.re_ASSERT, lambda m: InterpretationParser.code_IF.format(
            cnd='not ' + m.group(1),
            bdy='throw "' + m.group(2) + '";',
        ))
        eol = self._match_replace(eol, InterpretationParser.re_CHECK, self._replace_CHECK)
        eol = self._match_replace(eol, InterpretationParser.re_ASIL, self._replace_ASIL)
        return eol

    def _parse_eol_exp(self, eol):
        return self._parse_eol_stmt(eol)

    def _parse_exp_or_stmt(self, str_or_arr):
        if type(str_or_arr) is str:
            return self._parse_eol_exp(str_or_arr)
        else:
            return self._parse_eol_stmts(str_or_arr)


    def _normalize_ocl(self, req_id):
        dict_val_to_array(self._ocl, 'pre')
        dict_val_to_array(self._ocl, 'post')
        self._ocl.setdefault('guard', [])

        self._normalize_expand_ocl(req_id)

        # Look for SPECIAL keywords in values and statements
        self._ocl['pre'] = self._parse_eol_stmts(self._ocl['pre'])
        self._ocl['post'] = self._parse_eol_stmts(self._ocl['post'])
        self._ocl['guard'] = self._parse_exp_or_stmt(self._ocl['guard'])

        # normalize OCL entry
        # Look for context aware keywords
        for ocl_t in self._ocl['ts']:
            ocl_t['t'] = self._parse_exp_or_stmt(ocl_t['t'])
            ocl_t['guard'] = self._parse_exp_or_stmt(ocl_t.get('guard', []))
            dict_remove_if_empty_list(ocl_t, 'guard')

        dict_remove_if_empty_list(self._ocl, 'guard')

    def _normalize_expand_ocl(self, req_id):
        # expand it
        default_msg = 'ISO requirement: ' + self.iso_req_model.get_text(req_id,
                                                                        'Missing from context.requirement_files')
        default_msg = dict_poll(self._ocl, 'message', default_msg)
        # normalize OCL['ts']
        if 't' in self._ocl:
            # Replace t <- ts
            t = {
                't': self._ocl['t'],
            }
            t.update(dict_poll_all_if_present(self._ocl, 'name', 'message', 'fix'))
            self._ocl['ts'] = [t]
            del self._ocl['t']
        elif 'ts' not in self._ocl:
            self._ocl['ts'] = []
        # normalize all elements in OCL['ts']
        ts = []
        for t in self._ocl['ts']:
            if type(t) is str:
                # Replace ts strings by dicts
                t = {'t': t}
            t['message'] = '"%s: %s"' % (req_id, t.get('message', default_msg))
            if 'fix' in t:
                t['fix'] = dict_val_to_array(t, 'fix')
                for f in t['fix']:
                    if type(f['action']) is not list:
                        f['action'] = [f['action'] + ';', ]
                    f['title'] = '"%s"' % f['title']
            ts.append(t)
        self._ocl['ts'] = ts

    def write_json(self):
        filename = self.get_context('json_output_file')
        # original = json.load(open(filename))
        json.dump({
            'model_refs': self.model_refs,
        }, open(filename, 'w+'))


def main():
    if len(sys.argv) > 1:
        inter = InterpretationParser()
        inter.load(sys.argv[1])
        inter.parse()
        inter.normalize()
        inter.write_json()

        return

    inter = InterpretationParser()
    # inter.load('ISO_model/interpretation_test.yaml')
    # inter.load('ISO_model/interpretation.yaml')
    inter.load('/home/dennis/Dropbox/0cn/ISO_model/interpretation_fsc.yaml')
    inter.validate()
    inter.parse()
    inter.normalize()
    inter.validate_normalized()
    inter.write_json()
    for ref, req_id in sorted(inter.model_refs.items()):
        print('%s: %s' % (ref, req_id))


if __name__ == '__main__':
    main()
