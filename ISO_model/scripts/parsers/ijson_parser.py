import json

from jsonschema import validate as json_scheme_validate
from ISO_model.scripts.parsers.parser import Parser
from ISO_model.scripts.schemes.simple_model_inst_list_scheme import ModelInstanceIdList


class IJsonParser(Parser):
    def __init__(self):
        self.o = {}

    def load(self, file_name):
        o = json.load(open(file_name))
        assert self.o.setdefault('class_name', o['class_name']) == o['class_name']
        self.o.setdefault('instances', {}).update(o['instances'])

    def parse(self):
        pass

    def validate(self):
        s = ModelInstanceIdList.get_schema()
        json_scheme_validate(self.o, s)

    def get(self):
        return self.o
