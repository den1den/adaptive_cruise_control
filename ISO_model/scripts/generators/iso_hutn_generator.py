import json

from ISO_model.scripts.generators.hutn_generator import HutnGenerator
from ISO_model.scripts.parsers.ijson_parser import IJsonParser


def class_name_to_hutn_prefix(class_name):
    cln_capitals = ''.join(filter(str.isupper, class_name))
    if len(cln_capitals) >= 2:
        return cln_capitals.lower()
    else:
        return class_name[:2].lower()


class IsoModelHutnGenerator(HutnGenerator):
    def __init__(self, clauses: IJsonParser, work_products: IJsonParser, other_inputs: IJsonParser):
        super(IsoModelHutnGenerator, self).__init__()
        self.requirements = {}
        self.clauses = clauses
        self.work_products = work_products
        self.other_inputs = other_inputs

    def load(self, iso_json):
        self.requirements.update(json.load(open(iso_json)))

    def generate(self, outfile):
        self.out = open(outfile, 'w+')
        self.clauses.validate()
        self.work_products.validate()
        self.other_inputs.validate()

        self.print_package('iso_model')
        self.print_block('iso_model')

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

    def generate_complete(self, outfile):
        self.out = open(outfile, 'w+')
        self.clauses.validate()
        self.work_products.validate()
        self.other_inputs.validate()

        self.print_package('iso_model')
        self.print_block('iso_model')
        self.print_block('Iso26262', self.generate_iso_element)
        self._finish()

    def generate_iso_element(self):
        parts = [c['id'].split('-')[0]
                 for c in self.clauses.get_with_id()]
        parts = list(sorted(set(parts)))
        requirements = [{'id': rid, 'name': r.get('title')}
                        for rid, r in sorted(self.requirements.items())]

        self.print_attr_array(
            'parts', 'Part',
            lambda p: 'p' + p,
            lambda p: self.generate_part(p),
            parts
        )
        self.print_attr_array(
            'clauses', 'Clause',
            lambda c: 'cl' + c['id'],
            lambda c: self.generate_clause(c),
            self.clauses.get_with_id()
        )
        self.print_model_instances(self.work_products, 'work_products')
        self.print_model_instances(self.other_inputs, 'other_inputs')
        self.print_attr_array(
            'requirements', 'IsoRequirement',
            lambda r: 'ir' + r['id'],
            lambda r: self.values(r, ('id', 'name')),
            requirements
        )

    def generate_part(self, p):
        clauses = [c for c in self.clauses.get_with_id()
                   if c['id'].startswith(str(p))]
        self.print_kv('id', str(p))
        self.print_kv('clauses', [c['id'] for c in clauses], 'Clause')

    def generate_clause(self, c):
        requirements = [
            {'id': rid, 'name': r.get('title')}
            for rid, r in sorted(self.requirements.items())
            if rid.startswith(c['id'])]

        self.print_kv('id', c['id'])
        self.print_kv('name', c['name'])
        self.print_kv('requirements', [r['id'] for r in requirements], 'IsoRequirement')
        self.print_kv('work_product_input', c['work_product_input'], 'WorkProductType')
        self.print_kv('other_input', c['other_input'], 'Input')


def main():
    work_products = IJsonParser()
    work_products.load(r'ISO_model/work_products.json')
    clauses = IJsonParser()
    clauses.load(r'ISO_model/clauses.json')
    other_inputs = IJsonParser()
    other_inputs.load('ISO_model/other_input.json')

    g = IsoModelHutnGenerator(clauses, work_products, other_inputs)
    g.load('ISO_model/generated/ISO-1-text.json')
    g.load('ISO_model/generated/ISO-3-text.json')
    g.load('ISO_model/generated/ISO-8-text.json')
    g.generate_complete(r'data_models/model/iso/iso_model/generated/iso26262-complete.hutn')


if __name__ == '__main__':
    main()
