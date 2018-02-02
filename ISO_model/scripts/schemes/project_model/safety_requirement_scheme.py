import json

from jsl import DocumentField

from ISO_model.scripts.schemes.schemes import *

REQUIREMENT_LEVELS = ['SG', 'FSR', 'TSR', 'HSR', 'SSR']


# Generic requirement specification class
class RequirementsSpecFile(DictField):
    def __init__(self, doc_cls):
        super().__init__(properties={
            'requirements_type': String(),
            'requirements': DictField(
                properties={'default': DocumentField(doc_cls, as_ref=True, required=False)},
                pattern_properties={'_': DocumentField(doc_cls, as_ref=True)},
            ),
        })


# Generic requirement list class
class RequirementsListFile(DictField):
    def __init__(self, doc_cls):
        super().__init__(properties={
            'requirements': DictField(
                properties={'default': DocumentField(doc_cls, as_ref=True, required=False)},
                pattern_properties={'_': DocumentField(doc_cls, as_ref=True)},
            ),
        })


# Specific classes

class NormalRequirementSpec(jsl.Document):
    description = String(required=False)
    allocated_to = SingleOrArray(String(), required=False)
    req_class = String(required=False)
    children = ChildrenInDocumentField()
    parent = String(required=False)
    notation = String(required=False)


class NormalRequirementStrict(jsl.Document):
    description = String()
    req_id = String()
    req_class = String(required=False)
    allocated_to = ArrayField(String())
    parent = String(required=False)
    notation = String()

    requirement_file = String()
    requirement_type = String()


# Specification
class SafetyRequirementSpec(jsl.Document):
    description = String(required=False)
    notation = String(required=False)
    derrived_from = ArrayField(String(), required=False, min_items=0)
    allocated_to_item = String(required=False)
    status = String(required=False)
    asil = String(required=False)
    level = String(required=False)
    # only for specification:
    children = ChildrenInDocumentField()
    # ignored
    priority = String(required=False)


# Strict
class SafetyRequirementStrict(jsl.Document):
    description = String(required=True)
    notation = String(required=True)
    derrived_from = ArrayField(String(), min_items=0, required=True),
    allocated_to_item = String(required=True)
    allocated_to_element = ArrayField(String(), required=True, min_items=0)
    status = String(required=True)
    asil = String(required=True)
    level = String(required=True)
    # Also required:
    req_id = String(required=True)

    group = String(required=True)
    # Grouping will be done per component
    # ISO: Organisation of safety requirements means that safety requirements within each level are grouped together,
    # usually corresponding to the architecture.

    requirement_type = String(required=True)  # safety requirement or not


if __name__ == '__main__':
    s = RequirementsSpecFile(SafetyRequirementSpec).get_schema()
    json.dump(s, open('/home/dennis/Dropbox/0cn/ISO_model/generated/safety_requirement_spec_scheme.json', 'w+'))

    s = RequirementsListFile(SafetyRequirementStrict).get_schema()
    json.dump(s, open('/home/dennis/Dropbox/0cn/ISO_model/generated/safety_requirement_strict_scheme.json', 'w+'))

    s = RequirementsSpecFile(NormalRequirementSpec).get_schema()
    json.dump(s, open('/home/dennis/Dropbox/0cn/ISO_model/generated/normal_requirement_spec_scheme.json', 'w+'))

    s = RequirementsListFile(NormalRequirementStrict).get_schema()
    json.dump(s, open('/home/dennis/Dropbox/0cn/ISO_model/generated/normal_requirement_strict_scheme.json', 'w+'))
