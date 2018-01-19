import json
import re

import sys


class EmfaticParser:
    re_namespace = re.compile(r'@namespace\(.*\)')
    re_comment_block = re.compile(r'/\*(?:(?:[^*])|(?:\*[^/]))*\*/')
    re_comment = re.compile(r'//.*$', re.MULTILINE)
    re_package = re.compile(r'package \w+;')
    re_class = re.compile(r'(abstract )?class (\w+)\s*(?:extends (\w+)\s*)?{([^}]*)}')
    re_statement = re.compile(r'(\w+) (\w+(?:\[(?:\*|(?:\d(?:..[\d*])?))?\])?) (\w+);')
    re_enum = re.compile(r'enum (\w+)\s*{\s*([^}]*)}')
    re_enum_statements = re.compile(r'(\w+);\s*')

    def __init__(self):
        self.abstract_classes = set()
        self.extensions = {}
        self.enums = {}
        self._doc_str = ''
        self.atts = {}

    def parse_file(self, filename=r'/home/dennis/Dropbox/0cn/acc_mm/model/project/project_model.emf'):
        lines = '\n'.join([l for l in open(filename)])
        lines = re.sub('[ \t]+', ' ', lines)
        lines = re.sub('\n+', '\n', lines)
        self._doc_str = lines
        self._parse()

    def _parse(self):
        self._skip_comments()
        self._re_skip(EmfaticParser.re_namespace)
        self._skip_comments()
        self._re_skip(EmfaticParser.re_package)

        while True:
            if self._skip_comments():
                continue
            if self._match_class():
                continue
            if self._match_enum():
                continue
            break

        if self._doc_str != "":
            print("Emfatic parser could not parse: `%s`" % (self._doc_str,))

    def _skip_comments(self):
        self._skip_whitespace()
        m = EmfaticParser.re_comment_block.match(self._doc_str)
        if m:
            self._doc_str = self._doc_str[m.end():]
            return True
        m = EmfaticParser.re_comment.match(self._doc_str)
        if m:
            self._doc_str = self._doc_str[m.end():]
            return True
        return False

    def _skip_whitespace(self):
        self._doc_str = self._doc_str.lstrip()

    def _re_skip(self, rep):
        self._skip_whitespace()
        m = rep.match(self._doc_str)
        if not m:
            raise AssertionError("Could not match `%s`" % rep)
        self._doc_str = self._doc_str[m.end():]

    def _match_class(self):
        m = EmfaticParser.re_class.match(self._doc_str)
        if not m:
            return None
        class_abstract = m.group(1) is not None
        class_name = m.group(2)
        class_super = m.group(3)
        class_body = m.group(4)
        if class_super:
            self.extensions[class_name] = class_super
        if class_abstract:
            self.abstract_classes.add(class_name)
        self._match_class_contents(class_name, class_body)
        self._doc_str = self._doc_str[m.end():]
        return True

    def _match_class_contents(self, class_name, txt):
        self.atts.setdefault(class_name, {})
        for m in EmfaticParser.re_statement.finditer(txt):
            a_rel = m.group(1)
            a_type = m.group(2)
            a_name = m.group(3)
            self.atts[class_name][a_name] = a_type

    def _match_enum(self):
        m = EmfaticParser.re_enum.match(self._doc_str)
        if not m:
            return None
        enum_name = m.group(1)
        enum_statements = m.group(2)
        stmts = []
        for stmt in EmfaticParser.re_enum_statements.finditer(enum_statements):
            stmts.append(stmt.group(1))
        self.enums[enum_name] = stmts
        self._doc_str = self._doc_str[m.end():]
        return True

    def get_all_subclasses(self, super_class: str):
        super_classes = {super_class}
        while True:
            n0 = len(super_classes)
            for sub_c, super_c in self.extensions.items():
                if super_c in super_classes:
                    super_classes.add(sub_c)
            n1 = len(super_classes)
            if n0 == n1:
                return super_classes

    def has_att(self, class_name, attribute_name):
        return self.atts.get(class_name, {}).get(attribute_name, False)

    def class_is_subclass_of(self, class_name, super_class):
        class_name = class_name.split('[')[0]
        while True:
            if class_name == super_class:
                return True
            if class_name not in self.extensions:
                return False
            class_name = self.extensions[class_name]

    def check_conforms(self, interpretation):
        check = True
        for class_name, atts in self.atts.items():
            for att_name, att_class in atts.items():
                att_ref = class_name + '.' + att_name
                if not att_ref in interpretation.model_refs:
                    print('Emfatic file has un interpreted attribute: ' + att_ref)
                    check = False
        return check


def main():
    if len(sys.argv) > 1:
        ep = EmfaticParser()
        ep.parse_file(sys.argv[1])

        from ISO_model.scripts.extract_interpretation import InterpretationParser
        ip = InterpretationParser()
        ip.load_interpretation_yaml()  # from default location

        if not ep.check_conforms(ip):
            raise AssertionError("Emfatic file does not conform to interpretation")
        return

    ep = EmfaticParser()
    ep.parse_file()

if __name__ == '__main__':
    main()
