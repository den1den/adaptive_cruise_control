import json
import jsl

from ISO_model.schemes.schemes import *


class ModelFields(jsl.DictField):
    def __init__(self):
        super().__init__(pattern_properties={
            # no two __
            '(?!.*([_])\1).*': jsl.AnyOfField([
                jsl.StringField(),
                jsl.ArrayField(jsl.StringField())
            ]),
            '__refs_to_id': jsl.StringField(),
        })


class ModelInstanceList(jsl.Document):
    """
    class_name with instances (dict or list)
    """
    class_name = jsl.StringField(required=True)
    hutn_id_prefix = jsl.StringField()
    instances = jsl.AnyOfField([
        jsl.ArrayField(ModelFields()),  # either array without ids
        jsl.DictField(pattern_properties={'': ModelFields()})  # or dict with ids
    ], required=True)


class ModelInstanceIdList(ModelInstanceList):
    """
    keys of instances are the id
    """
    instances = jsl.DictField(pattern_properties={'': ModelFields()}, required=True)


if __name__ == '__main__':
    s = ModelInstanceIdList.get_schema()
    # s = ModelInstanceList.get_schema()
    print(json.dumps(s, indent=2))
