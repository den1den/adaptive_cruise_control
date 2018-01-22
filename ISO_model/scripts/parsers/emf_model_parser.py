import json
import re

import sys

from ISO_model.scripts.parsers.parser import Parser


class EmfModelParser(Parser):
    re_namespace = re.compile(r'@namespace\(.*\)')
    re_comment_block = re.compile(r'/\*(?:(?:[^*])|(?:\*[^/]))*\*/')
    re_comment = re.compile(r'//.*$', re.MULTILINE)
    re_package = re.compile(r'package \w+;')
    re_class = re.compile(r'(abstract )?class (\w+)\s*(?:extends (\w+)\s*)?{([^}]*)}')
    re_statement = re.compile(r'(\w+) (\w+(?:\[(?:\*|(?:\d(?:..[\d*])?))?\])?) (\w+);')
    re_enum = re.compile(r'enum (\w+)\s*{\s*([^}]*)}')
    re_enum_statements = re.compile(r'(\w+);\s*')

    def __init__(self):
        self.interpretation_json = {}
        self.abstract_classes = set()
        self.extensions = {}
        self.enums = {}
        self._doc_str = ''
        self.atts = {}
        self.context = {}

    def load(self, file_name):
        lines = [l for l in open(file_name)]
        # Extract context
        json_match = re.match(r'\s*//\s*({\s*"context".*)', lines[0])
        if json_match:
            for c_key, c_val in json.loads(json_match.group(1))['context'].items():
                if type(c_val) is list:
                    self.context.setdefault(c_key, []).extend(c_val)
                else:
                    self.context.setdefault(c_key, []).append(c_val)
            lines = lines[1:]
        # Normalize whitespace
        lines = '\n'.join(lines)
        lines = re.sub('[ \t]+', ' ', lines)
        lines = re.sub('\n+', '\n', lines)
        self._doc_str = lines

    def parse(self):
        self._skip_comments()
        self._re_skip(EmfModelParser.re_namespace)
        self._skip_comments()
        self._re_skip(EmfModelParser.re_package)

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
        m = EmfModelParser.re_comment_block.match(self._doc_str)
        if m:
            self._doc_str = self._doc_str[m.end():]
            return True
        m = EmfModelParser.re_comment.match(self._doc_str)
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
        m = EmfModelParser.re_class.match(self._doc_str)
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
        for m in EmfModelParser.re_statement.finditer(txt):
            a_rel = m.group(1)
            a_type = m.group(2)
            a_name = m.group(3)
            self.atts[class_name][a_name] = a_type

    def _match_enum(self):
        m = EmfModelParser.re_enum.match(self._doc_str)
        if not m:
            return None
        enum_name = m.group(1)
        enum_statements = m.group(2)
        stmts = []
        for stmt in EmfModelParser.re_enum_statements.finditer(enum_statements):
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

    def check_conforms(self):
        interpretation_json = {}
        for i_file in self.context.get('interpretation_files', []):
            for key, val in json.load(open(i_file)).items():
                interpretation_json.setdefault(key, {}).update(val)

        check = True
        for class_name, atts in self.atts.items():

            if self.class_is_subclass_of(class_name, 'Artifact'):
                continue

            if len(atts) == 0:
                if class_name not in interpretation_json['model_refs']:
                    print('Emfatic file has an class which is never referenced: %s' % class_name)
                    check = False
            for att_name, att_class in atts.items():
                att_ref = class_name + '.' + att_name
                if att_ref not in interpretation_json['model_refs']:
                    print('Emfatic file has un interpreted attribute: %s' % att_ref)
                    check = False
        return check

    emf_model_for_scheme = None

    @staticmethod
    def set_for_scheme(filename):
        i = EmfModelParser()
        i.load(filename)
        i.parse()
        EmfModelParser.emf_model_for_scheme = i
        print("EmfModelParser.set_default attributes=\n%s" % i.get_all_attribute_notations())

    def get_all_attribute_notations(self):
        all_attributes = []
        # Add all: Class, Class.att, Class.att[*]
        for class_name, class_attributes in self.atts.items():
            all_attributes.append(class_name)
            for attribute_name, attribute_class in class_attributes.items():
                all_attributes.append(class_name + '.' + attribute_name)
                if '[' in attribute_class:
                    cardinality = '[' + attribute_class.split('[')[1]
                    all_attributes.append(class_name + '.' + attribute_name + cardinality)
                else:
                    all_attributes.append(class_name + '.' + attribute_name + '[0..1]')
        # Add all: Enum, Enum.VAL
        for enum_name, enum_vals in self.enums.items():
            all_attributes.append(enum_name)
            for enum_val in enum_vals:
                all_attributes.append(enum_name + '.' + enum_val)
        return all_attributes

    def get_all_classes(self):
        all_classes = []
        for class_name, class_attributes in self.atts.items():
            if class_name not in self.abstract_classes:
                all_classes.append(class_name)
        for enum_name, enum_vals in self.enums.items():
            all_classes.append(enum_name)
        return all_classes


def main():
    if len(sys.argv) > 1:
        emf_model = EmfModelParser()
        emf_model.load(sys.argv[1])
        emf_model.parse()
        if not emf_model.check_conforms():
            print("Warnings in %s:\n" % sys.argv[1], file=sys.stderr)
            exit(-1)
        return

    emf_model = EmfModelParser()
    #emf_model.load(r'/home/dennis/Dropbox/0cn/data_models/model/project/project_model.emf')
    emf_model.load(r'/home/dennis/Dropbox/0cn/data_models/model/project/fsc_project_model.emf')
    emf_model.parse()
    if not emf_model.check_conforms():
        print("\nEmfatic file does not conform to interpretation", file=sys.stderr)
        exit(-1)


if __name__ == '__main__':
    main()
