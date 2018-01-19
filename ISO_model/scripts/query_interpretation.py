from ISO_model.scripts.extract_interpretation import InterpretationParser


class Query:
    def __init__(self) -> None:
        self.interpretation = InterpretationParser()

    def load_interpretation(self):
        self.interpretation.load_interpretation_yaml()

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
    q.load_interpretation()
    while True:
        attr = input('Search for a attribute (Item.description):\n')
        q.query_used(attr)
