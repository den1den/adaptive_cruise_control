import jsl  # http://jsl.readthedocs.io/en/latest/tutorial.html

# http://json-schema.org/implementations.html
# npm install -g pajv
from jsl import Document
from jsl.document import DocumentMeta

from ISO_model.scripts.extract_emfatic import EmfaticParser

re_REQUIREMENT_ID = r'\d(\.\d)*'
"""Ex: 4.1"""
re_FULL_REQUIREMENT_ID = r'\d-\d(\.\d)*'
"""Ex: 3-4.1"""


class Enum(jsl.StringField):
    def __init__(self, values_list, **kwargs):
        super().__init__(enuum=values_list, **kwargs)


class AnyDict(jsl.DictField):
    def __init__(self, *to_fields, **kwargs):
        kwargs.setdefault('pattern_properties', {
            '': AnyOf(*to_fields)
        })
        super(AnyDict, self).__init__(**kwargs)


class SameTargetDict(jsl.DictField):
    def __init__(self, *keys, to, **kwargs):
        super(SameTargetDict, self).__init__(
            {key: to for key in keys},
            **kwargs)


class SimpleDict(jsl.DictField):
    def __init__(self, properties, **kwargs):
        super(SimpleDict, self).__init__(
            properties,
            **kwargs)


class DictIgnore_(jsl.DictField):
    """A document with ignores _ affix in the keys"""

    def __init__(self, properties: dict, **kwargs):
        extra_prop = {}
        # extra_prop.update({key + '(_\w*)?': val for key, val in kwargs.get('pattern_properties', {}).items()})
        extra_prop.update({key + r'(_\w*)?': val for key, val in properties.items()})
        kwargs['pattern_properties'] = extra_prop
        super(DictIgnore_, self).__init__(**kwargs)


class RequirementId(jsl.StringField):
    def __init__(self, **kwargs):
        kwargs['pattern'] = re_REQUIREMENT_ID
        super().__init__(**kwargs)


def _get_model_reference_enum():
    emf_parser = EmfaticParser()
    emf_parser.parse_file('/home/dennis/Dropbox/0cn/acc_mm/model/project/project_model.emf')
    enum = []
    for class_name, atts in emf_parser.atts.items():
        enum.append(class_name)
        for attribute_name, attribute_class in atts.items():
            enum.append(class_name + '.' + attribute_name)
            if '[' in attribute_class:
                cardinality = '[' + attribute_class.split('[')[1]
                enum.append(class_name + '.' + attribute_name + cardinality)
            else:
                enum.append(class_name + '.' + attribute_name + '[0..1]')
    for enum_name, enum_vals in emf_parser.enums.items():
        enum.append(enum_name)
        for enum_val in enum_vals:
            enum.append(enum_name + '.' + enum_val)
    print("Using strict ModelReferenceField with enum =\n%s" % enum)
    return enum


class ModelReference(jsl.StringField):
    strict = True

    def __init__(self, **kwargs):
        if ModelReference.strict:
            kwargs['enum'] = _get_model_reference_enum()
        else:
            kwargs['pattern'] = r'^[A-Z]\w*(\.\w*)*(\[\d(..(\d|\*))?\])?$'
        kwargs.setdefault('title', 'References to elements in the project model')
        kwargs.setdefault('description', 'References to elements in the project model')
        kwargs.setdefault('min_length', 1)
        super(ModelReference, self).__init__(**kwargs)


class ModelClassName(jsl.StringField):
    def __init__(self, **kwargs):
        kwargs.setdefault('title', 'A class name')
        super(ModelClassName, self).__init__(**kwargs)


class EolBool(jsl.StringField):
    def __init__(self, **kwargs):
        kwargs.setdefault('title', 'Eol boolean value')
        kwargs.setdefault('min_length', 1)
        super(EolBool, self).__init__(**kwargs)


class EolStatements(jsl.StringField):
    def __init__(self, **kwargs):
        kwargs.setdefault('Eol commands, referencing utils.eol file')
        kwargs.setdefault('min_length', 1)
        super(EolStatements, self).__init__(**kwargs)


class AnyOf(jsl.AnyOfField):
    def __init__(self, *any_of, **kwargs):
        instances = [
            jsl.DocumentField(d) if type(d) is DocumentMeta else  # fix missing DocumentField casts
            d() if type(d) is type else  # fix missing instantiations
            d for d in any_of
        ]
        super(AnyOf, self).__init__(
            instances,
            **kwargs)


class ArrayField(jsl.ArrayField):
    """Array of any of the `items`"""

    def __init__(self, *any_of, **kwargs):
        kwargs.setdefault('min_items', 1)
        kwargs.setdefault('unique_items', True)
        super().__init__(
            AnyOf(*any_of),
            **kwargs)


class SingleOrArray(AnyOf):
    def __init__(self, *any_of, **kwargs):
        super(SingleOrArray, self).__init__(
            *any_of,
            ArrayField(*any_of, min_items=1),
            **kwargs)


def doc_field(document_class, **kwargs):
    return jsl.DocumentField(document_class, **kwargs)
