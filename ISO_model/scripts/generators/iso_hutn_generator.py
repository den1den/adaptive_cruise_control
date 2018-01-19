import json

import sys

from ISO_model.scripts.generators.hutn_generator import HutnGenerator
from ISO_model.scripts.parsers.ijson_parser import IJsonParser


def class_name_to_hutn_prefix(class_name):
    cln_capitals = ''.join(filter(str.isupper, class_name))
    if len(cln_capitals) >= 2:
        return cln_capitals.lower()
    else:
        return class_name[:2].lower()


class IsoModelHutnGenerator(HutnGenerator):
    def __init__(self, clauses, work_products) -> None:
        super(IsoModelHutnGenerator, self).__init__()
        self.requirements = {}
        self.clauses = clauses
        self.work_products = work_products

    def load(self, iso_json):
        self.requirements.update(json.load(open(iso_json)))

    def generate(self, outfile=None):
        if outfile:
            self.out = open(outfile, 'w+')
        else:
            self.out = sys.stdout

        self.clauses.validate()
        self.work_products.validate()

        self._print('@Spec { metamodel "iso_research" { nsUri: "iso_research" } }')
        self._print()

        package = 'project_model'
        package = 'iso_model'
        self._print(package + ' {', 1)

        # Requirements
        for r_id, r in sorted(self.requirements.items()):
            if any((r['annotations'].get(a, False) for a
                    in ('ignore', 'work_product'))):
                continue
            r['name'] = r['title']
            r.setdefault('id', r_id)
            self.inst_with_id('IsoRequirement', r, ('id', 'name'))

        self.print_model_instances(self.clauses)
        self.print_model_instances(self.work_products)

        self._finish()


def main():
    work_products = IJsonParser()
    work_products.load(r'ISO_model/generated/work_products.json')
    clauses = IJsonParser()
    clauses.load(r'ISO_model/clauses.json')

    g = IsoModelHutnGenerator(clauses, work_products)
    g.load('ISO_model/generated/part3-text.2.json')
    g.generate(r'data_models/model/iso/iso_model/generated/iso26262.hutn')


if __name__ == '__main__':
    main()
