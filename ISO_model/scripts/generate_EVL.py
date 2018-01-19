import json
import os
import re

import sys
import yaml

from ISO_model.schemes.interpretation_scheme import InterpretationDocument
from jsonschema.validators import validate as json_scheme_validate

from ISO_model.schemes.schemes import ModelReference
from ISO_model.scripts.extract_emfatic import EmfaticParser


class EVLDocumentGenerator:

    def __init__(self, outfile) -> None:
        self.out = open(outfile, 'w+')
        self.indent = 0

    def _print(self, line=None, indent_inc=0):
        if line:
            print('\t' * self.indent + line, file=self.out)
        else:
            print(file=self.out)
        self.indent += indent_inc

    def p_close_block(self):
        self.indent -= 1
        self._print('}')

    def p_open_block(self, title):
        self._print(title + ' {', 1)

    def p_block(self, title, fn):
        self.p_open_block(title)
        fn()
        self.p_close_block()

    def _finish(self):
        for i in range(self.indent):
            self.p_close_block()
        self.out.close()

    def p_comment(self, msg: str):
        self._print('// %s' % msg)

    def p_comment_heading(self, header: str):
        N = 80
        self._print('/'*N)
        self._print('// '+(header+' ').ljust(N-3, '/'))
        self._print('/'*N)

    # EVL specific:

    def p_inform(self, msg: str):
        self._print('inform("%s")' % msg)

    def sanitize_name(self, name: str):
        name = name.replace('+', 'p').replace('-', 'm').replace('.', '_')
        if name[0].isdigit():
            name = 'n' + name
        return name

    def p_context(self, name, guards=None, constraints=None, pre=None, post=None):
        name = self.sanitize_name(name)
        if pre:
            self.p_open_block('pre ' + name)
            self.p_statements(pre)
            self.p_close_block()
        self.p_open_block('context ' + name)
        self.p_expression_or_block('guard', guards)

        for c in constraints:
            self.p_constraint(**c)

        self.p_close_block()
        if post:
            self.p_open_block('post ' + name)
            self.p_statements(pre)
            self.p_close_block()

    def p_constraint(self, name, guards=None, checks=None, messages=None, fixes=None):
        name = self.sanitize_name(name)
        # constraint or critique
        self.p_open_block('constraint %s' % name)
        self.p_expression_or_block('guard', guards)
        self.p_expression_or_block('check', checks)
        self.p_expression_or_block('message', messages)
        if fixes:
            for fix in fixes:
                self.p_fix(fix['titles'], fix['statements'], fix.get('guards'))
        self.p_close_block()

    def p_fix(self, title, statements, guard=None):
        self.p_open_block('fix')

        self.p_expression_or_block('guard', guard)
        self.p_expression_or_block('title', title)

        self.p_open_block('do')
        for s in statements:
            self._print(s)
        self.p_close_block()

        self.p_close_block()

    def p_expression_or_block(self, keyword, var):
        if var is None:
            return
        if type(var) is str:
            self._print('%s : %s' % (keyword, var))
        else:
            self.p_open_block(keyword)
            for s in var:
                self._print(s)
            self.p_close_block()

    def p_statements(self, var):
        if type(var) is str:
            self._print(var)
        else:
            for s in var:
                self._print(s)


def get_single_or_array(d: dict, key):
    val = d.get(key, [])
    if type(val) is not list:
        val = [val]
    return val


class InterpretationEVLGenerator(EVLDocumentGenerator):
    eol_var_name = '[a-z_][a-zA-Z0-9_]*'
    eol_class_name = '[a-zA-Z0-9_]*'
    eol_value = '(?:{cls}\.)?{var}'.format(cls=eol_class_name, var=eol_var_name)
    re_possible_att = re.compile(r'^CHECK\s+({var})$'.format(var=eol_var_name))
    re_DEFINE = re.compile(r'DEFINE\s+((?:{var}\.)?{var})\s+({value})'.format(var=eol_var_name, value=eol_value))

    def __init__(self, outfile) -> None:
        super(InterpretationEVLGenerator, self).__init__(outfile)
        self.ocl_per_level = {}
        self.interpretation = {'requirements': {}}

        self.model = EmfaticParser()
        self.model.parse_file('/home/dennis/Dropbox/0cn/acc_mm/model/project/project_model.emf')

    def load_requirements_yaml(self, *files):
        scheme = InterpretationDocument().get_schema()
        for file in files:
            i_doc = yaml.safe_load(open(file))
            json_scheme_validate(i_doc, scheme)
            # silent overwrite
            for key, vals in i_doc.items():
                if key.startswith('requirement'):
                    self.interpretation['requirements'].update(vals)

    def _interpret_ocl(self, req_id, ocl_level, ocl_root: dict, init_pre: list, init_post: list):
        # Each OCL entry defines a context
        context = {
            'pre': init_pre + ocl_root.get('pre', []),
            'post': init_post + ocl_root.get('post', []),
            'name': ocl_root['c'],
            'guards': ocl_root.get('g'),  # None, str or list
            'constraints': []
        }
        i = 0
        default_name = '%s_%s_%s' % (req_id, ocl_level, i)
        if 't' in ocl_root:  # normalize
            ocl_root['ts'] = [{
                't': ocl_root['t'],
                'name': ocl_root.get('name', default_name)
            }]
        for t in ocl_root['ts']:
            # Add a constraint
            if type(t) is str:
                # Most simpe one
                constraint = {
                    'name': default_name,
                    'guards': None,
                    'checks': t,
                    'messages': None,
                    'fixes': None,
                }
            else:
                constraint = {
                    'name': t.get('name', default_name),
                    'guards': t.get('g'),
                    'checks': t['t'],
                    'messages': t.get('messages'),
                    'fixes': t.get('fixes'),
                }
            self._process_constraint(constraint, context)

            context['constraints'].append(constraint)
            i += 1
            default_name = '%s_%s_%s' % (req_id, ocl_level, i)

        self._process_context(context)
        self.ocl_per_level.setdefault(ocl_level, {})
        self.ocl_per_level[ocl_level].setdefault(req_id, [])
        self.ocl_per_level[ocl_level][req_id].append(context)

    def _process_context(self, context):
        context['pre'] = [self._process_eol(p) for p in context['pre']]
        context['post'] = [self._process_eol(p) for p in context['post']]

    def _process_eol(self, eol):
        found = True
        while found:
            m = InterpretationEVLGenerator.re_DEFINE.finditer(eol)
            found = False
            for m in m:
                var_name = m.group(1)
                value_name = m.group(2)
                l = 'if({var_name}.isUndefined()){{{var_name}={value_name};}}'.format(
                    var_name=var_name, value_name=value_name)
                eol = eol[:m.start()] + l + eol[m.end():]
                found = True
        return eol

    def _process_constraint(self, constraint, context):
        # Parse the constraint
        constraint_text = constraint['checks']
        item_class = context['name']
        m = InterpretationEVLGenerator.re_possible_att.match(constraint_text)
        if m:
            item_attribute = m.group(1)
            ac = self.model.has_att(item_class, item_attribute)
            assert ac
            assert self.model.class_is_subclass_of(ac, 'Check')
            # Interpret check attribute keyword
            check_class = ac
            # Generate pre
            create_missing_evl = (
                    'for (x : {item_class} in {item_class}.all().select(x|x.{item_attribute}.isUndefined()) ) {{' +
                    ' x.{item_attribute} = new {check_class}; ' +
                    '}}'
            ).format(item_class=item_class, item_attribute=item_attribute, check_class=check_class)
            context['pre'] += [
                '// CREATE '+item_class+'.'+item_attribute,
                create_missing_evl,
                '//'
            ]
            # Overwrite check
            constraint['checks'] = (
                'self.{item_attribute}.checked'
            ).format(item_attribute=item_attribute)

    def generate(self):
        for req_id, req_interpretation in self.interpretation['requirements'].items():
            for ocl_level, ocl_roots in req_interpretation.get('ocl', {}).items():
                for ocl_root in ocl_roots:
                    self._interpret_ocl(
                        req_id, ocl_level, ocl_root,
                        init_pre=req_interpretation.get('pre', []), init_post=req_interpretation.get('post', [])
                    )

        # print main document structure
        for ocl_level, o_r in sorted(self.ocl_per_level.items()):
            self.p_comment_heading("ocl level " + ocl_level)
            for req_id, contexts in sorted(o_r.items()):
                self.p_comment(ocl_level+" requirement " + req_id)
                for context in contexts:
                    self.p_context(**context)



def main():
    ModelReference.verbose = False

    if len(sys.argv) > 1:
        interpretation_file = sys.argv[1]
        file_base = os.path.splitext(os.path.basename(interpretation_file))[0]
        g = InterpretationEVLGenerator('acc_mm/model/acc/CHECK_%s.evl' % file_base)
        g.load_requirements_yaml(interpretation_file)
        g.generate()
        return


    g = InterpretationEVLGenerator('../../acc_mm/model/acc/TEST.evl')
    g.load_requirements_yaml('../interpretation_test.yaml', )
    #g.load_requirements_yaml('../interpretation.yaml', )
    print()
    print('------------------------------------')
    print()
    g.generate()


if __name__ == '__main__':
    main()
