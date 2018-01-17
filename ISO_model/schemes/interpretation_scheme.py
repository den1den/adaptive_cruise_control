import json

from ISO_model.schemes.schemes import *


class Definition(jsl.Document):
    pr_model = ArrayField([
        ModelReferenceField(),
    ], required=True)
    prs_pre = ModelEolField()


RequirementClassification = jsl.StringField(enum=[
    'manual',  # project model specification
    'ocl',  # OCL spec
    'work_product',  # project model specification
    'pm',  # project model specification
    'iso',  # iso model specification
    'to high',  # To high level, skipped
])


class Requirement(jsl.Document):
    status = jsl.StringField(enum=['gen', 'todo'], required=True)
    classification = jsl.ArrayField(RequirementClassification, unique_items=True)
    pr_model = ArrayField([
        # doc_field(Definition, as_ref=True),
        ModelReferenceField(),
        doc_field(Definition()),
        # , Definition(as_ref=True) # jsl.fields.RefField()
    ])
    pr_validation = ArrayField([
        ModelValidationField()
    ])
    prd_satisfies = ArrayField([
        ModelEolField()
    ])
    prd_suggestion_satisfies = ArrayField([
        ModelEolField()
    ], min_items=0)
    prs_pre = ArrayField([
        ModelEolField()
    ])
    ignored = jsl.StringField()
    introduces = jsl.DictField()
    child = jsl.StringField()  # Children have the same pr_needs
    context = jsl.IntField(minimum=1)


class WorkProductInterp(jsl.Document):
    pass


class InterpretationDict(DictIgnore_):

    def __init__(self):
        super().__init__({
            'definitions': ArrayField([
                doc_field(Definition())
            ], required=True, min_items=0),
            'requirements': jsl.DictField(pattern_properties={
                re_REQUIREMENT_ID: doc_field(Requirement)
            }, required=True),
            'work_products': jsl.DictField(pattern_properties={
                re_REQUIREMENT_ID: doc_field(WorkProductInterp)
            })
        })


if __name__ == '__main__':
    s = InterpretationDict().get_schema()
    print(json.dumps(s, indent=2))
