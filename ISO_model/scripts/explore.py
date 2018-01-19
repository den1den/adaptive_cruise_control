"""
Deprecated
"""
import json
import os
import re

import yaml

from ISO_model.scripts.extract_OCL import tokenize
from ISO_model.scripts.parsers.iso_text_parser import IsoTextParser


class DefSearcher:
    re_w1 = re.compile(r'(\w+)(?:\s|$)')

    def __init__(self, infile) -> None:
        self.output = []
        self.infile = infile
        self.element = None

    def search(self):
        with open(self.infile) as f:
            for l in f:
                self.parse_l(l)
        self.findrefs()
        return self.output

    def parse_l(self, line):
        m = IsoTextParser.re_title.match(line)
        if m:
            # prepare next
            self.element = {
                'id': m.group(1),
                'title': m.group(2).strip(),
                'lines': [],
            }
            self.output.append(self.element)
            return

        self.element['lines'] += [line]

    def findrefs(self):
        terms = {el['title']: el for el in self.output}

        requirements = 0
        reqs_with_ref = 0

        referenced_terms = []
        for el in self.output:
            uses_ref = False
            for l in el['lines']:
                l = l.strip()
                tokens = tokenize(l)['tokens']

                while True:
                    found = False
                    for i, size in all_combos_array(tokens):
                        # large to small
                        partial_term = ' '.join(tokens[i:i + size])
                        if partial_term in terms:
                            referenced_terms.append(partial_term)
                            print("%s -----> %s" % (l[0:30], partial_term))
                            tokens = tokens[:i] + tokens[i + size:]
                            found = True
                            uses_ref = True
                            break
                    if not found:
                        break
            requirements += 1
            if uses_ref:
                reqs_with_ref += 1
            else:
                print("NO REF ------> %s" % el)

        referenced_terms = set(referenced_terms)

        for existing_term in referenced_terms:
            for sub_term in all_word_combos(existing_term):
                if sub_term in terms:
                    # There are term clashes: "failure, random hardware failure"
                    print("Found referenced term %s which is also part of %s" % (existing_term, sub_term))
                    pass

        print("%d of %d requirements uses a reference" % (reqs_with_ref, requirements))
        print("%d distinct references are used" % (len(referenced_terms)))


def all_word_combos(string):
    tr = tokenize(string)
    tokens = tr['tokens']
    for i, size in all_combos_array(tokens):
        yield ' '.join(tokens[i:i + size])


def all_combos_array(arr, exclude_full=True):
    max_size = len(arr)
    if exclude_full:
        max_size -= 1
    for size in range(max_size, 0, -1):
        for i in range(len(arr) - size + 1):
            yield (i, size)


def fix_clauses():
    clause_regex = re.compile('(\d)-(\d)\s(.*)')
    out = {}
    for c in json.load(open('../clauses.json')):
        m = clause_regex.match(c)
        c = {
            'part': m.group(1),
            'section': m.group(2),
            'name': m.group(3),
        }
        out["%s-%s" % (c['part'], c['section'])] = c
    json.dump(out, open('../clauses.2.json', 'w+'), indent=2, sort_keys=True)


def explore_iso_generation():
    infile = 'ISO_model/part3-text.json'
    outfile = 'ISO_model/part3-model.yaml'
    if os.path.exists(outfile):
        raise Exception("file %s already exists, this is only for first generation" % outfile)
    iso_json = json.load(open(infile))
    out = []
    for requirement in iso_json:
        out.append({
            'constraints': ['%s.evl' % requirement['id']],
            'a_iso_requirement': requirement['id'],
        })
    yaml.dump(out, open(outfile, 'w'), indent=2)


def print_all_requirement_ids():
    reqs = {}
    reqs.update(json.load(open('ISO_model/generated/part3-text.json')))
    for rid in sorted(reqs.keys()):
        print(rid)


def main():
    print_all_requirement_ids()
    return

    fix_clauses()

    s = DefSearcher('../part1-text.2.txt')
    r = s.search()
    for l in r:
        # print(l)
        pass


if __name__ == '__main__':
    main()
