import os
import sys

import yaml
from jsonschema.validators import validate as json_scheme_validate

from ISO_model.schemes.schemes import *

RequirementClassifications = (
    'structure',  # specifies structure of the project
    'ocl',
    'weak_ocl',  # ocl by cheating in a Checked class
    'existence',  # specifies the existence of certain elements
    'to high',  # To high level, skipped
    'act',  # specifies an activity to perform
    'work_product',
)

RequirementInterpretationStatuses = (
    'gen',  # initially generated
    'todo',  # still working on
    'skip'  # considered unimportant
    'checked',  # verified
)

OCLLevels = (
    '++', '+', 'o',  # from a table
    'suggested', 'satisfies',  # from the iso text
    'warning',  # possible assumed pitfalls
    'needs',  # assumptions on the project instance structure
)

EOLTest = EolBool(description='the EOL check', required=True)


class EOLSingleCheckWithName(jsl.Document):
    t = EOLTest
    name = jsl.StringField(description='Name of the constraint, default: ReqId_Context_Index')
    g = EolBool(description='Filters the constraint')
    message = jsl.StringField(description='Message to display on failure')
    # `pre` is not supported here


class OCLConstraintBase(jsl.Document):  # abstract
    # Common
    c = ModelClassName(description='The EVL context', required=True)
    pre = ArrayField(EolStatements, description='@pre actions for this context')
    g = EolBool(description='Filters the context')


class OCLConstraintForClass(OCLConstraintBase):
    # can be specified with test and name
    t = EOLTest
    name = jsl.StringField(description='Name of the constraint, default: ReqId_Context_Index')
    # the g is taken from the Context class only


class OCLConstraintsForClass(OCLConstraintBase):
    # or can be specified as list of tests (possible with names)
    ts = ArrayField(
        EOLTest, EOLSingleCheckWithName,
        description='Multiple EOL checks', required=True)


class InterpretationRequirement(jsl.Document):
    """
    These define the interpretation of an iso requirement
    """
    status = Enum(RequirementInterpretationStatuses)
    quality = jsl.StringField(
        description='Documentation on the quality of the interpretation')
    classification = jsl.ArrayField(
        Enum(RequirementClassifications), unique_items=True)
    ignored = jsl.StringField(
        description='Documentation on a part if the requirement which is ignored')
    assumed = jsl.StringField(
        description='Documentation on certain assumptions which are made')
    introduces = jsl.DictField(
        description='Documentation on possible introduced concepts')
    context = jsl.IntField(  # Deprecated: overkill
        minimum=1,
        description='The number of parent requirement which are needed to understand this requirement')
    pr_model = SingleOrArray(
        ModelReference(),
        description='References to parts of the model which are created when interpreting this requirement')
    pre = ArrayField(
        EolStatements,
        description='@pre actions for each context. ' +
                    'These actions can possibly create parts of the project instance which are needed later on')
    ocl = SameTargetDict(
        *OCLLevels,
        to=ArrayField(
            OCLConstraintForClass,
            OCLConstraintsForClass,
        ),
        description='Contains keys with the level of satisfaction to a set of constraints to satisfy that level')


class InterpretationWorkProduct(jsl.Document):
    """
    Some information about the interpretation of a work product
    """

    class Options:
        additional_properties = True


class InterpretationDocument(DictIgnore_):
    """The root of the interpretation document contains these keys"""

    def __init__(self):
        super().__init__({
            'requirements': jsl.DictField(
                pattern_properties={re_REQUIREMENT_ID: doc_field(InterpretationRequirement)},
                required=True),
            'work_products': jsl.DictField(
                pattern_properties={re_REQUIREMENT_ID: doc_field(InterpretationWorkProduct)},
                required=True),
        })


if __name__ == '__main__':
    import json

    ModelReference.silent = False
    s = InterpretationDocument().get_schema()

    # Save scheme
    json.dump(s, open('/home/dennis/Dropbox/0cn/ISO_model/generated/interpretation_scheme.json', 'w+'), indent=2)
    print("Scheme created")

    if len(sys.argv) > 1:
        # Check scheme against provided *.yaml file
        filename = sys.argv[1]
        if filename.endswith('.yaml'):
            inst = yaml.safe_load(open(filename))
            json_scheme_validate(inst, s)
            print("%s is valid" % os.path.basename(filename))
