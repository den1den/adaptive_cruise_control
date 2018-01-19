import yaml

from ISO_model.schemes.interpretation_scheme import InterpretationDocument
from ISO_model.scripts.extract_emfatic import EmfaticParser
from jsonschema.validators import validate as json_scheme_validate

class Query:
    def __init__(self) -> None:
        self.interpretation = {'requirements': {}}

        self.model = EmfaticParser()
        self.model.parse_file('/home/dennis/Dropbox/0cn/acc_mm/model/project/project_model.emf')

    def load_requirements_yaml(self, *files):
        scheme = InterpretationDocument().get_schema()
        for file in files:
            i_doc = yaml.safe_load(open(file))
            json_scheme_validate(i_doc, scheme)
            # silent overwrite
            for key, vals in i_doc.items():
                if key.startswith('requirement'):
                    self.interpretation['requirements'].update(vals)

    def query_used(self, attribute):
        found = False
        for rid, r_spec in self.interpretation['requirements'].items():
            if attribute in r_spec.get('pr_model', []):
                print("Found in "+rid)
                found = True
                continue

        if not found:
            print("Not found")

        print()


if __name__ == '__main__':
    q = Query()
    q.load_requirements_yaml('../interpretation.yaml')
    while True:
        attr = input('Search for a attribute (Item.description):\n')
        q.query_used(attr)
