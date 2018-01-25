from ISO_model.scripts.schemes.schemes import *


class ContextDocument(DictField):
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
    import json

    s = ContextDocument().get_schema()

    # Save scheme
    json.dump(s, open('/home/dennis/Dropbox/0cn/ISO_model/generated/context_scheme.json', 'w+'), indent=0)
    print("Context scheme created")
