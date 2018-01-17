import jsl  # http://jsl.readthedocs.io/en/latest/tutorial.html

# http://json-schema.org/implementations.html
# npm install -g pajv

re_REQUIREMENT_ID = r'\d(\.\d)*'
re_FULL_REQUIREMENT_ID = r'\d-\d(\.\d)*'


class AnyDict(jsl.DictField):

    def __init__(self, to_fields: list, **kwargs):
        super(AnyDict, self).__init__(pattern_properties={
            '': jsl.AnyOfField(to_fields)
        }, **kwargs)


class SimpleDict(jsl.DictField):

    def __init__(self, properties, **kwargs):
        super(SimpleDict, self).__init__(properties, **kwargs)


class DictIgnore_(jsl.DictField):
    """A document with ignores _ affix in the keys"""

    def __init__(self, properties: dict, **kwargs):
        extra_prop = {}
        #extra_prop.update({key + '(_\w*)?': val for key, val in kwargs.get('pattern_properties', {}).items()})
        extra_prop.update({key + r'(_\w*)?': val for key, val in properties.items()})
        kwargs['pattern_properties'] = extra_prop
        super(DictIgnore_, self).__init__(**kwargs)


class RequirementId(jsl.StringField):
    def __init__(self, **kwargs):
        kwargs['pattern'] = re_REQUIREMENT_ID
        super().__init__(**kwargs)


class ModelReferenceField(jsl.StringField):
    def __init__(self, **kwargs):
        kwargs['pattern'] = r'^[A-Z]\w*(\.\w*)*(\[\d(..(\d|\*))?\])?$'
        kwargs['title'] = r'References to elements in the project model'
        kwargs['description'] = r'References to elements in the project model'
        super(ModelReferenceField, self).__init__(**kwargs)


class ModelEolField(jsl.StringField):
    def __init__(self, **kwargs):
        kwargs['title'] = 'Eol commands, referencing utils.eol file'
        super(ModelEolField, self).__init__(**kwargs)


class ModelValidationField(jsl.StringField):
    def __init__(self, **kwargs):
        kwargs['title'] = 'Eol commands for validation, referencing utils.eol file'
        super(ModelValidationField, self).__init__(**kwargs)


class ArrayField(jsl.ArrayField):
    def __init__(self, classes: list, **kwargs):
        kwargs.setdefault('min_items', 1)
        super().__init__(jsl.AnyOfField(classes), **kwargs)


def doc_field(document_class, **kwargs):
    return jsl.DocumentField(document_class, **kwargs)
