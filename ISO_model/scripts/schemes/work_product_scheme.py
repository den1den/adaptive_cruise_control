import json
from .schemes import *


class WorkProduct(jsl.Document):
    name = jsl.StringField(required=True)
    based_on = ArrayField(
        RequirementId,
    )


class WorkProducts(jsl.DictField):
    def __init__(self, **kwargs):
        kwargs['pattern_properties'] = {
            re_FULL_REQUIREMENT_ID: doc_field(WorkProduct())  # Work product id (Ex: 3-5.5)
        }
        super().__init__(**kwargs)


if __name__ == '__main__':
    s = WorkProducts().get_schema()
    print(json.dumps(s, indent=2))
