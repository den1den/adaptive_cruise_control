import sys

import json

import yaml

from ISO_model.scripts.lib.util import dict_update
from ISO_model.scripts.parsers.emf_model_parser import EmfModelParser
from ISO_model.scripts.schemes.schemes import *

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


class EOLSingleCheckWithName(DictField):
    def __init__(self):
        super().__init__(properties={
            't': EolBool(description='the EOL check', required=True),
            'name': jsl.StringField(description='Name of the constraint, default: ReqId_Context_Index'),
            'g': EolBool(description='Filters the constraint'),
            'messages': jsl.StringField(description='Message to display on failure'),
            # `pre` is not supported here
        })


class OCLConstraintBase(DictField):
    def __init__(self, properties: dict = None):
        super(OCLConstraintBase, self).__init__(properties=dict_update({
            # Common
            'c': ModelClassName(description='The EVL context', required=True),
            'pre': EolStatements(
                description='@pre actions for this context. ' +
                            'These actions can possibly create parts of the project instance which are needed later on'),
            'post': EolStatements(),
            'g': EolBool(description='Filters the context'),
        }, properties))


class OCLPreForClass(OCLConstraintBase):
    def __init__(self):
        super(OCLPreForClass, self).__init__(properties={
            'pre': EolStatements(required=True),
        })


class OCLConstraintForClass(OCLConstraintBase):
    def __init__(self):
        super(OCLConstraintForClass, self).__init__(properties={
            # can be specified with test and name
            't': EolBool(description='the EOL check', required=True),
            'name': jsl.StringField(description='Name of the constraint, default: ReqId_Context_Index'),
            # the g is taken from the Context class only
        })


class OCLConstraintsForClass(OCLConstraintBase):
    def __init__(self):
        super().__init__(properties={
            # or can be specified as list of tests (possible with names)
            'ts': ArrayField(
                EolBool(description='the EOL check'),
                EOLSingleCheckWithName,
                description='Multiple EOL checks', required=True
            ),
        })


class OclLevelDict(SameTargetDict):
    def __init__(self, *to, **kwargs):
        kwargs.setdefault('description',
                          'Contains keys with the level of satisfaction to a set of constraints to satisfy that level')
        super(OclLevelDict, self).__init__(
            *OCLLevels,
            to=ArrayField(*to, min_items=kwargs.get('min_properties')),
            **kwargs,
        )


class InterpretationRequirementBase(DictField):
    """
    These define the interpretation of an iso requirement
    """

    def __init__(self, properties: dict):
        super(InterpretationRequirementBase, self).__init__(dict_update({
            'status': Enum(RequirementInterpretationStatuses),
            'quality': jsl.StringField(
                description='Documentation on the quality of the interpretation'),
            'classification': ArrayField(
                Enum(RequirementClassifications), unique_items=True),
            'ignored': jsl.StringField(
                description='Documentation on a part if the requirement which is ignored'),
            'assumed': jsl.StringField(
                description='Documentation on certain assumptions which are made'),
            'introduces': jsl.DictField(
                description='Documentation on possible introduced concepts'),
            'context': jsl.IntField(  # Deprecated: overkill
                minimum=1,
                description='The number of parent requirement which are needed to understand this requirement'),
            'pr_model': SingleOrArray(
                ModelReference(),
                description='References to parts of the model which are created when interpreting this requirement'),
        }, properties))


class InterpretationRequirement(InterpretationRequirementBase):
    def __init__(self):
        super().__init__(properties={
            'ocl': OclLevelDict(
                OCLConstraintForClass,
                OCLConstraintsForClass,
                OCLPreForClass,
                required=False,
            ),
        })


class InterpretationRequirementWithPre(InterpretationRequirementBase):
    def __init__(self):
        super().__init__(properties={
            'ocl': OclLevelDict(
                OCLConstraintForClass,
                OCLConstraintsForClass,
                OCLPreForClass,
                OCLConstraintBase,  # Also a single class is allowed as pre will be automatically filled
                required=True,
                min_properties=1,
            ),  # When pre is specified at least one OCL (or EVL 'context') must be present to execute it
            'pre': EolStatements(required=True),
        })


class InterpretationWorkProduct(DictField):
    """
    Some information about the interpretation of a work product
    """


class InterpretationScheme(DictField):
    """The root of the interpretation document contains these keys"""

    def __init__(self):
        super().__init__(properties={
            'requirements': DictField(
                pattern_properties={
                    re_FULL_REQUIREMENT_ID: AnyOf(InterpretationRequirement(), InterpretationRequirementWithPre())
                },
            ),
            'work_products': DictField(
                pattern_properties={
                    re_FULL_REQUIREMENT_ID: AnyOf(InterpretationWorkProduct())
                },
                required=False
            ),
            'context': jsl.DictField(),
        })


def main():
    if len(sys.argv) > 2:
        # assert the document is already valid w.r.t. context
        context_document = yaml.safe_load(open(sys.argv[1]))
        EmfModelParser.set_default(context_document.get('context', {}).get('file_model'))
        output = sys.argv[2]
    else:
        output = '/home/dennis/Dropbox/0cn/ISO_model/generated/interpretation_scheme.json'

    s = InterpretationScheme().get_schema()
    json.dump(s, open(output, 'w+'), indent=1)

    # Save scheme
    print("Interpretation scheme created in %s" % output)


if __name__ == '__main__':
    main()