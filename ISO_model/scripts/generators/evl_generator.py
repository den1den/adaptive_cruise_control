import datetime
import os
import re
import sys

from ISO_model.scripts.generators.eol_generator import EolGenerator
from ISO_model.scripts.parsers.emf_model_parser import EmfModelParser


class EvlGenerator(EolGenerator):

    def __init__(self) -> None:
        super().__init__()
        self.used_uniques = {}

    def p_inform(self, msg: str):
        self._print('inform("%s")' % msg)

    def sanitize_name(self, name: str):
        name = name.replace('+', 'p').replace('-', 'm').replace('.', '_')
        if name[0].isdigit():
            name = 'n' + name
        return name

    def get_unique(self, name_type, name):
        d = self.used_uniques.setdefault(name_type, {})
        prev = d.get(name)
        if prev:
            name = '%s_%s' % (name, prev)
        else:
            prev = 0
        d[name] = prev + 1
        return name

    def p_context(self, name, guards=None, constraints=None, pre=None, post=None):
        name = self.sanitize_name(name)
        if pre:
            self.p_open_block('pre ' + self.get_unique('pre', name))
            self.p_statements(pre)
            self.p_close_block()
        self.p_open_block('context ' + name)

        self.p_expression_or_block('guard', guards)
        for c in constraints:
            self.p_constraint(**c)

        self.p_close_block()
        if post:
            self.p_open_block('post ' + self.get_unique('post', name))
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
                self.p_fix(**fix)
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


class InterpretationEVLGenerator(EvlGenerator):
    eol_var_name = '[a-z_][a-zA-Z0-9_]*'
    eol_class_name = '[a-zA-Z0-9_]*'
    eol_value = '(?:{cls}\.)?{var}'.format(cls=eol_class_name, var=eol_var_name)
    re_possible_att = re.compile(r'^CHECK\s+({var})$'.format(var=eol_var_name))
    re_DEFINE = re.compile(r'DEFINE\s+((?:{var}\.)?{var})\s+({value})'.format(var=eol_var_name, value=eol_value))

    def __init__(self, interpretation) -> None:
        super(InterpretationEVLGenerator, self).__init__()
        self.ocl_per_level = {}
        self.ip = interpretation
        self.out = open(self.ip.get_context('evl_output_file'), 'w+')

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
        for t in ocl_root['ts']:
            # Add a constraint
            constraint = {
                'name': t.get('name', default_name),
                'guards': t.get('g'),
                'checks': t['t'],
                'messages': t.get('messages'),
                'fixes': t.get('fixes'),
            }

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

    def generate(self):
        for req_id, req_interpretation in self.ip.interpretation['requirements'].items():
            for ocl_level, ocl_roots in req_interpretation.get('ocl', {}).items():
                for ocl_root in ocl_roots:
                    self._interpret_ocl(
                        req_id, ocl_level, ocl_root,
                        init_pre=req_interpretation.get('pre', []), init_post=req_interpretation.get('post', [])
                    )

        # print main document structure
        self.p_comment('Generated at %s' % datetime.datetime.now())
        for ocl_level, o_r in sorted(self.ocl_per_level.items()):
            self.p_comment_heading("ocl level " + ocl_level)
            for req_id, contexts in sorted(o_r.items()):
                self.p_comment(ocl_level+" of requirement " + req_id)
                for context in contexts:
                    self.p_context(**context)


def main():
    from ISO_model.scripts.parsers.interpretation_parser import InterpretationParser

    if len(sys.argv) > 1:
        interpretation_file = sys.argv[1]
        i = InterpretationParser()
        i.load(interpretation_file)
        i.parse()
        i.normalize()

        g = InterpretationEVLGenerator(i)
        g.generate()

        print("Generated: %s" % i.get_context('evl_output_file'))
        return

    i = InterpretationParser()
    i.load('ISO_model/interpretation_test.yaml')
    i.parse()
    i.validate()
    i.normalize()
    i.validate_normalized()

    g = InterpretationEVLGenerator(i)
    g.generate()


if __name__ == '__main__':
    main()
