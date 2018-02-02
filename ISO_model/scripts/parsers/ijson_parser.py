import json

from jsonschema import validate as json_scheme_validate

from ISO_model.scripts.lib.util import dict_update
from ISO_model.scripts.parsers.parser import Parser
from ISO_model.scripts.schemes.simple_model_inst_list_scheme import ModelInstanceIdList


class IJsonParser(Parser):
    def __init__(self):
        self.output = {}

    def load(self, file_name):
        o = json.load(open(file_name))
        assert self.output.setdefault('class_name', o['class_name']) == o['class_name']
        self.output.setdefault('instances', {}).update(o['instances'])

    def parse(self):
        pass

    def validate(self):
        s = ModelInstanceIdList.get_schema()
        json_scheme_validate(self.output, s)

    def get(self):
        return self.output

    def get_with_id(self):
        return [dict_update(obj, {'id': i}) for i, obj in self.output['instances'].items()]
