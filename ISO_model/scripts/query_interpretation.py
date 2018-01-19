from ISO_model.scripts.parsers.interpretation_parser import InterpretationParser


class Query:
    def __init__(self) -> None:
        self.ip = InterpretationParser()
        self.ip.load()
        self.ip.parse()
        # Full interpretation needed? self.ip.to_json()

    def query_used(self, attribute):
        found = False
        for rid, r_spec in self.ip.interpretation['requirements'].items():
            if attribute in r_spec.get('pr_model', []):
                print("Found in "+rid)
                found = True
                continue

        if not found:
            print("Not found")

        print()


if __name__ == '__main__':
    q = Query()
    while True:
        attr = input('Search for a attribute (Item.description):\n')
        q.query_used(attr)
