import sys

import json

import yaml

from ISO_model.scripts.lib.util import dict_update
from ISO_model.scripts.parsers.emf_model_parser import EmfModelParser
from scripts.schemes.schemes import *

RequirementClassifications = (
    'from_dennis',  # virtual requirement for the creation of checking and auxiliary instantiations
    'from_arash',  # virtual requirement interpreted by the model of TNO
    'structure_intro',  # (just) introduces elements of the project structure
    'structure',  # specifies structure of the project
    'ocl',  # specifies some kind of constraint
    'act',  # specifies some sort of activity
    'vague',  # requirement needs some more explanation
    'clause_input',
    'work_product',
    'non_model',  # requirement should be verified manually, not using the model
)

RequirementInterpretationStatuses = (
    'gen',  # initially generated
    'assumed',  # assumed to be true
    'skip'  # considered unimportant
    'verified',  # verified
    'todo',  # still working on
)

OCLLevels = (
    '++', '+', 'o',  # from a table
    'suggested',  # from the iso text
    'satisfies',  # specified by the text (direct or indirect)
    'trivial',  # very simple OCL
    'structure',  # project instance structure (Ex: type(A.b)=B, or cardinal constraints)
    'warning',  # possible assumed pitfalls, (Warning should be given when OCL evaluates to true)
)


class EOLConstraint(DictField):
    def __init__(self):
        super().__init__(properties={
            't': EolValueOrStatements(
                description='the EOL check (block or single statement)',
                required=True,
            ),
            'name': jsl.StringField(
                description='Name of the constraint, default: ReqId_Context_Index',
            ),
            'guard': EolValueOrStatements(
                description='Filters the constraint',
            ),
            'message': EolValueOrStatements(
                description='Message to display on failure',
            ),
            # `pre` is not supported here
            'fix': SingleOrArray(Fix())
        })


class Fix(DictField):
    def __init__(self):
        super().__init__(properties={
            'guard': EolValueOrStatements(),
            'title': EolValueOrStatements(
                required=True,
            ),
            'action': EolStatementOrStatements(
                required=True,
            )
        })


class OCLContextBase(DictField):
    def __init__(self, properties: dict = None):
        super(OCLContextBase, self).__init__(properties=dict_update({
            # Common
            'c': ModelClassName(
                description='The EVL context',
                required=True,
            ),
            'guard': EolValueOrStatements(
                description='Filters the context',
            ),
            'pre': EolStatementOrStatements(
                description='pre actions for this context. ' +
                            'These actions can possibly create parts of the project instance which are needed later on',
            ),
            'post': EolStatementOrStatements(
                description='post actions for this context',
            ),
        }, properties))


class OCLContextSingleConstraint(OCLContextBase):
    def __init__(self):
        super(OCLContextSingleConstraint, self).__init__(properties={
            'name': jsl.StringField(
                description='Name of the constraint, default: ReqId_Context_Index',
            ),
            # guard is not possible for single constraint
            't': EolValueOrStatements(
                description='the EOL check',
                required=True,
            ),
            'message': EolValueOrStatements(
                description='Message to display on failure',
            ),
            'fix': SingleOrArray(Fix()),
        })


class OCLContextMultipleConstraints(OCLContextBase):
    def __init__(self):
        super().__init__(properties={
            # or can be specified as list of tests (possible with names)
            'ts': ArrayField(
                EolBool(description='the EOL check (only single statement allowed)'),
                EOLConstraint,
                description='Multiple EOL checks',
                required=True,
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
            'status': Enum(RequirementInterpretationStatuses, required=True),
            'quality': jsl.StringField(
                description='Documentation on the quality of the interpretation',
            ),
            'classification': ArrayField(
                Enum(RequirementClassifications),
                unique_items=True,
                min_items=0,
                required=True,
            ),
            'ignored': jsl.StringField(
                description='Documentation on a part if the requirement which is ignored',
            ),
            'assumed': jsl.StringField(
                description='Documentation on certain assumptions which are made',
            ),
            'introduces': jsl.DictField(
                description='Documentation on possible introduced concepts',
            ),
            'references': jsl.StringField(
                description='Reference to another ISO clause or Requirement',
            ),
            'context': jsl.IntField(  # Deprecated: overkill
                description='The number of parent requirement which are needed to understand this requirement',
                minimum=1,
            ),
            'activity': jsl.StringField(
                description='TODO: defines an activity',
            ),
            'extra_operations': EolStatements(
                description='These lines will be appended to the EVL file',
            ),
            'pr_model': SingleOrArray(
                ModelReference(),
                description='References to parts of the model which are created when interpreting this requirement',
            ),
        }, properties))


class InterpretationRequirement(InterpretationRequirementBase):
    def __init__(self):
        super().__init__(properties={
            'ocl': OclLevelDict(
                OCLContextSingleConstraint,
                OCLContextMultipleConstraints,
                required=False,
            ),
        })


class InterpretationRequirementWithPre(InterpretationRequirementBase):
    def __init__(self):
        super().__init__(properties={
            'ocl': OclLevelDict(
                OCLContextSingleConstraint,
                OCLContextMultipleConstraints,
                OCLContextBase,  # Also a single class is allowed as pre will be automatically filled
                required=True,
                min_properties=1,  # When pre/post is specified at least one context must be present to generate it
            ),
            'pre': EolStatementOrStatements(),
            'post': EolStatementOrStatements(),
        })


class InterpretationWorkProduct(DictField):
    """
    Some information about the interpretation of a work product
    """

    def __init__(self):
        super(InterpretationWorkProduct, self).__init__(
            additional_properties=True,  # Can be anything for now
        )


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
        EmfModelParser.emf_model_for_scheme = EmfModelParser()
        for emf_file in context_document['context']['model_files']:
            EmfModelParser.emf_model_for_scheme.load(emf_file)
        EmfModelParser.emf_model_for_scheme.parse()
        output = sys.argv[2]
    else:
        output = '/home/dennis/Dropbox/0cn/ISO_model/generated/interpretation_scheme.json'

    s = InterpretationScheme().get_schema()
    json.dump(s, open(output, 'w+'), indent=1)
    print("InterpretationScheme written to %s" % output)


if __name__ == '__main__':
    main()
