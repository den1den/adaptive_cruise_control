import os

import jsl  # http://jsl.readthedocs.io/en/latest/tutorial.html

# http://json-schema.org/implementations.html
# npm install -g pajv
from jsl.document import DocumentMeta

re_REQUIREMENT_ID = r'\d(\.\d)*'
"""Ex: 4.1"""
re_FULL_REQUIREMENT_ID = r'\d-\d(\.\d)*'
"""Ex: 3-4.1"""


class Enum(jsl.StringField):
    def __init__(self, values_list, **kwargs):
        super().__init__(enuum=values_list, **kwargs)


class DictField(jsl.DictField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('additional_properties', False)
        kwargs.setdefault('required', True)
        super().__init__(*args, **kwargs)


class SameTargetDict(DictField):
    def __init__(self, *keys, to, **kwargs):
        super(SameTargetDict, self).__init__(
            {key: to for key in keys},
            **kwargs)


class DictIgnore_(DictField):
    """A document with ignores _ affix in the keys"""

    def __init__(self, properties: dict, **kwargs):
        kwargs['properties'] = {}
        kwargs['pattern_properties'] = {key + r'(_\w*)?': val for key, val in properties.items()}
        super(DictIgnore_, self).__init__(**kwargs)


class RequirementId(jsl.StringField):
    def __init__(self, **kwargs):
        kwargs['pattern'] = re_REQUIREMENT_ID
        super().__init__(**kwargs)


class FileField(jsl.StringField):
    strict = True
    all_files_per_ext = {}

    def __init__(self, extension='', **kwargs):
        kwargs['pattern'] = '%s$' % extension.replace('.', '\.')
        if kwargs.get('must_exist', True) and FileField.strict:
            if extension not in FileField.all_files_per_ext:
                FileField.all_files_per_ext[extension] = [
                    os.path.relpath(os.path.join(dirpath, filename))
                    for dirpath, dirnames, filenames in os.walk('.')
                    for filename in filenames
                    if filename.endswith(extension)
                ]
                print("Identified %s files" % len(FileField.all_files_per_ext[extension]))
            kwargs['enum'] = FileField.all_files_per_ext[extension]
        kwargs.setdefault('min_length', 1)
        super(FileField, self).__init__(**kwargs)


class ModelReference(jsl.StringField):
    strict = True

    def __init__(self, **kwargs):
        if ModelReference.strict:
            from ISO_model.scripts.parsers.emf_model_parser import EmfModelParser
            kwargs['enum'] = EmfModelParser.emf_model_for_scheme.get_all_attribute_notations()
        else:
            kwargs['pattern'] = r'^[A-Z]\w*(\.\w*)*(\[\d(..(\d|\*))?\])?$'
        kwargs.setdefault('title', 'References to elements in the project model')
        kwargs.setdefault('description', 'References to elements in the project model')
        kwargs.setdefault('min_length', 1)
        super(ModelReference, self).__init__(**kwargs)


class ModelClassName(jsl.StringField):
    def __init__(self, **kwargs):
        kwargs.setdefault('title', 'A class name')
        if ModelReference.strict:
            from ISO_model.scripts.parsers.emf_model_parser import EmfModelParser
            kwargs['enum'] = EmfModelParser.emf_model_for_scheme.get_all_classes()
        super(ModelClassName, self).__init__(**kwargs)


class AnyOf(jsl.AnyOfField):
    def __init__(self, *any_of, **kwargs):
        instances = [
            jsl.DocumentField(d) if type(d) is DocumentMeta else  # fix missing DocumentField casts
            d() if type(d) is type else  # fix missing instantiations
            d for d in any_of
        ]
        super(AnyOf, self).__init__(instances, **kwargs)


class ArrayField(jsl.ArrayField):
    """Array of any of the `items`"""

    def __init__(self, *any_of, **kwargs):
        kwargs.setdefault('unique_items', True)
        super().__init__(
            AnyOf(*any_of),
            **kwargs)


class EolStatement(jsl.StringField):
    def __init__(self, **kwargs):
        kwargs.setdefault('title', 'Eol statement')
        super(EolStatement, self).__init__(**kwargs)


class EolValue(jsl.StringField):
    def __init__(self, **kwargs):
        kwargs.setdefault('title', 'Eol value')
        kwargs.setdefault('min_length', 1)
        super(EolValue, self).__init__(**kwargs)


class EolBool(EolValue):
    def __init__(self, **kwargs):
        kwargs.setdefault('title', 'Eol boolean value')
        super(EolBool, self).__init__(**kwargs)


class EolStatementOrStatements(AnyOf):
    def __init__(self, **kwargs):
        super().__init__(
            EolStatement,
            EolStatements,
            **kwargs,
        )


class EolValueOrStatements(AnyOf):
    def __init__(self, **kwargs):
        super(EolValueOrStatements, self).__init__(
            EolStatements(),
            EolValue(),
            **kwargs,
        )


class EolStatements(ArrayField):
    def __init__(self, **kwargs):
        kwargs.setdefault('description', 'Eol statements or comments, referencing utils.eol file')
        kwargs.setdefault('min_length', 0)
        kwargs.setdefault('unique_items', False)
        super(EolStatements, self).__init__(EolStatement, **kwargs)


class SingleOrArray(AnyOf):
    def __init__(self, *any_of, **kwargs):
        super(SingleOrArray, self).__init__(
            *any_of,
            ArrayField(*any_of, min_items=1),
            **kwargs)


def doc_field(document_class, **kwargs):
    return jsl.DocumentField(document_class, **kwargs)
