from ISO_model.scripts.schemes.schemes import *


class ContextDocument(DictField):
    """The root of the interpretation document contains these keys"""

    def __init__(self):
        super().__init__(properties={
            'context': DictField(properties={
                    'model_files': ArrayField(FileField('.emf'), required=True),
                    'evl_output_file': FileField('.evl', required=True),
                    'requirement_files': ArrayField(FileField('.txt')),
                    'normalized_output_file': FileField('.json'),
                    'file_test_instances': ArrayField(FileField()),  # Don't know yet
            })},
            additional_properties=True,
        )


if __name__ == '__main__':
    import json

    s = ContextDocument().get_schema()

    # Save scheme
    json.dump(s, open('/home/dennis/Dropbox/0cn/ISO_model/generated/context_scheme.json', 'w+'), indent=0)
    print("Context scheme created")
