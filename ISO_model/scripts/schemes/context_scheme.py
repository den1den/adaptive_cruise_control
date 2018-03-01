import json
import sys

from scripts.schemes.schemes import *


class ContextScheme(DictField):
    """The root of the interpretation document contains these keys"""

    def __init__(self):
        super().__init__(properties={
            'context': DictField(properties={
                # input files
                'model_files': ArrayField(FileField('.emf'), required=True, min_items=1),
                'requirement_files': ArrayField(FileField('.txt')),
                'extra_eol_files': ArrayField(FileField('.eol')),
                # output files
                'evl_output_file': FileField('.evl', must_exist=False, required=True),
                'normalized_output_file': FileField('.json', must_exist=False),
                'json_output_file': FileField('.json', must_exist=False),
                # Don't know yet
                'file_test_instances': ArrayField(FileField()),
            })},
            additional_properties=True,
        )


if __name__ == '__main__':
    s = ContextScheme().get_schema()

    # Save scheme
    output = sys.argv[1] if len(sys.argv) > 1 else '/home/dennis/Dropbox/0cn/ISO_model/generated/context_scheme.json'
    json.dump(s, open(output, 'w+'), indent=0)
    print("ContextScheme written to %s" % output)
