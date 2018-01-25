# converts a .txt file of ISO document to an json file
import json
import os
import re
import shutil

from jsonschema import validate as json_scheme_validate

from ISO_model.scripts.lib.util import dict_update, alpha_to_int
from ISO_model.scripts.schemes.simple_model_inst_list_scheme import ModelInstanceIdList
from ISO_model.scripts.parsers.parser import Parser


def str_rev(string: str):
    return ''.join(reversed(string))


class IsoTextParser(Parser):
    re_title = re.compile(r'^(\d{1,3}(?:\.\d{1,3}){1,5})\s*(.*)$')
    re_note = re.compile(r'^\s*NOTE\s*(.*)$')
    re_ordered_summation = re.compile(r'^\s*([a-z0-9]+)\)\s*(.*)$')
    re_unordered_summation = re.compile(r'^\s*⎯\s*(.*)$')
    re_example = re.compile(r'^\s*EXAMPLE\s*(?:\d+\s*)?(.*)$')
    re_annotation = re.compile(r'^([A-Z]+)>(.*)$')
    re_figure = re.compile(r'figure\s+(\d+)\s+—\s*(.*)', re.I)
    re_work_product = re.compile(r'\s*(.+)\s+as a result of requirements?\s+(.*)\s*', re.I)
    re_requirement_ref = re.compile(r'(\d+(?:\.\d+)+)\.?')
    re_simple_req_range = re.compile(r'(\d+(?:\.\d+)*)\.(\d+) to \1\.(\d+)\.?', re.I)
    re_simple_req_summation_rev = re.compile(r'\s*\.?([\d.]+) dna ([\d.]+)(?: ,([\d.]+))*', re.I)

    def __init__(self, read_from_annotations_file=None):
        self.lines = []
        self.output = {}
        self.annotations = json.load(open(read_from_annotations_file)) if read_from_annotations_file else {}
        self.work_products = {}  # Is not an input for this parser
        self.prev_line = None
        self.curr_line = None
        self.element = None
        self.missed_lines = []
        self.curr_SUM = None
        self.curr_ordered_SUM = None
        self.next_is_wp = False

    def load(self, text_file):
        id_prefix = re.match('.*ISO-?(\d+).*', text_file).group(1) + '-'
        self.lines += [{
            'text': line,
            'line_no': line_no,
            'prefix': id_prefix,
            'file': text_file,
        } for line_no, line in enumerate(open(text_file, 'r'))]

    def parse(self, print_all_lines=False):
        self.curr_line = None
        self.element = None

        self.missed_lines = []

        for l in self.lines:
            self.prev_line = self.curr_line
            self.curr_line = l
            if print_all_lines:
                print('parsing: ' + l['text'])
            self.parse_line()
        return len(self.missed_lines) == 0

    def parse_line(self):
        line_number = self.curr_line['line_no']
        text, annotation = self.parse_annotations(self.curr_line['text'])

        m = IsoTextParser.re_title.match(text)
        if m:
            # Requirement header found
            if self.element:
                # write previous element
                if len(self.missed_lines) > 0:
                    self.element['text'] = self.missed_lines
                    self.missed_lines = []

            # prepare next
            prefix = self.curr_line['prefix']
            rid = prefix + m.group(1)
            title = m.group(2).strip()
            self.element = {
                'id': rid,
                'title': title,
                'line_no': line_number,
            }

            if title == 'Work products':
                self.next_is_wp = True
                self.element['title'] = None
                annotation['ignore'] = True
            else:
                self.next_is_wp = False

            # store annotation
            annotation = dict_update(self.annotations.get(rid, {}), annotation)
            self.annotations[rid] = annotation

            # check ignore
            ignore = annotation.get('ignore', False)
            if not ignore:
                if rid in self.output:
                    raise AssertionError("Duplicate key '%s'" % rid)
                self.output[rid] = self.element

            # check work_product
            if not self.next_is_wp:
                self.parse_work_product()

            self.curr_SUM = None
            self.curr_ordered_SUM = None
            return
        else:
            if self.next_is_wp:
                self.element['title'] = text
                self.next_is_wp = False
                self.parse_work_product()

        # search notes
        m = IsoTextParser.re_note.match(text)
        if m:
            self.element.setdefault('notes', [])
            self.element['notes'] += [m.group(1)]
            return

        # search summation
        m = IsoTextParser.re_ordered_summation.match(text)
        if m:
            if self.curr_ordered_SUM is None:
                # start new summation
                self.curr_ordered_SUM = {
                    'title': self.prev_line,
                    'elements': [],
                    'ordered': True,
                }
                self.element.setdefault('sums', [])
                self.element['sums'] += [self.curr_ordered_SUM]

                # If the prev_line is not missed because its the title of this sum
                self._unmis_line(self.prev_line['line_no'])

            self.curr_ordered_SUM['elements'] += [{
                'index': m.group(1),
                'text': m.group(2),
                'line_no': line_number,
            }]
            return
        else:
            self.curr_ordered_SUM = None

        m = IsoTextParser.re_unordered_summation.match(text)
        if m:
            if self.curr_SUM is None:
                # start new summation
                self.curr_SUM = {
                    'title': self.prev_line,
                    'elements': [],
                    'ordered': False,
                }
                self.element.setdefault('sums', [])
                self.element['sums'] += [self.curr_SUM]

                if not IsoTextParser.re_title.match(self.prev_line['text']):
                    self._unmis_line(self.prev_line['line_no'])

            self.curr_SUM['elements'] += [{
                'text': m.group(1),
                'line_no': line_number,
            }]
            return
        else:
            self.curr_SUM = None

        # search example
        m = IsoTextParser.re_example.match(text)
        if m:
            self.element.setdefault('examples', [])
            self.element['examples'] += [m.group(1)]
            return

        self.missed_lines.append(self.curr_line)

    def parse_work_product(self):
        title = self.element['title']
        rid = self.element['id']
        prefix = self.curr_line['prefix']
        ann_work_product = self.annotations[rid].get('work_product', False)
        m = IsoTextParser.re_work_product.match(title)
        if ann_work_product or m:
            if not m:
                raise AssertionError(
                    "Work product fail '%s' to %s" % (title, IsoTextParser.re_work_product))
            work_product_name = m.group(1)
            work_product_range = m.group(2)

            WP = {
                'name': work_product_name,
                'based_on': work_product_range,
            }

            while True:
                rm = IsoTextParser.re_simple_req_range.match(work_product_range)
                if rm:
                    base = rm.group(1)
                    WP['based_on__refs_to_id'] = 'IsoRequirement'
                    WP['based_on'] = [prefix + '%s.%d' % (base, digit) for digit in
                                      range(int(rm.group(2)), int(rm.group(3)))]
                    break
                rm = IsoTextParser.re_simple_req_summation_rev.match(str_rev(work_product_range))
                if rm:
                    WP['based_on__refs_to_id'] = 'IsoRequirement'
                    WP['based_on'] = [prefix + str_rev(r) for r in reversed(rm.groups())]
                    break
                rm = IsoTextParser.re_requirement_ref.match(work_product_range)
                if rm:
                    WP['based_on__refs_to_id'] = 'IsoRequirement'
                    WP['based_on'] = [prefix + rm.group(1)]
                    break
                break

            self.work_products[rid] = WP

    boolean_annotations = {
        'I': 'ignore',
        'H': 'header',
        'W': 'work_product',
    }

    def parse_annotations(self, line):
        m = IsoTextParser.re_annotation.match(line)
        annotation = {}
        if m:
            annotation_str = m.group(1)
            for char in annotation_str:
                if char in IsoTextParser.boolean_annotations:
                    annotation[IsoTextParser.boolean_annotations[char]] = True
                else:
                    raise AssertionError("Unknown annotation '%s' in %s" % (char, self.curr_line))
            line = m.group(2)
        return line, annotation

    def _unmis_line(self, line_no):
        unmis = []
        for l in self.missed_lines:
            if l['line_no'] == line_no:
                unmis.append(l)
        for l in unmis:
            self.missed_lines.remove(l)

    def write_iso_json(self, out_filename):
        if len(self.missed_lines) > 0:
            raise Exception("Parsing failed")
        # Also append annotations
        output = {
            rid: dict_update(o, {
                'annotations': self.annotations[o['id']]
            }) for rid, o in self.output.items()
        }
        json.dump(output, open(out_filename, 'w+'), indent=2, sort_keys=True)

    def var_dump_annotations(self, output):
        """Write updated annotation file to output"""
        non_zero_annotations = {
            key: val for key, val in self.annotations.items() if len(val) > 0
        }
        json.dump(non_zero_annotations, open(output, 'w+'), indent=2, sort_keys=True)

    def print(self):
        for req_id, r in sorted(self.output.items()):
            print("%s\t%d\t%s" % (str(req_id).ljust(10), int(r['line_no']), r['title']))

    def var_dump_work_products(self, filename):
        """Not in correct format, just a var dump"""
        json.dump(self.work_products, open(filename, 'w+'), indent=2, sort_keys=True)

    def write_work_products(self, filename):
        work_ps = {
            'class_name': "WorkProductType",
            'instances': self.work_products,
        }
        json_scheme_validate(work_ps, ModelInstanceIdList.get_schema())
        json.dump(work_ps, open(filename, 'w+'), indent=2, sort_keys=True)

    def get_text(self, req_id: str, default):
        r = self.output.get(req_id)
        appendix = ''
        if r is None:
            # try parent
            req_id = [s for s in req_id.split('.')]
            req_parent = '.'.join(req_id[:-1])
            tumor = req_id[-1]
            r = self.output.get(req_parent)
            if r is None:
                return default
            if 'sums' in r:
                if len(r['sums']) == 1:
                    appendix = r['sums'][0]['elements'][alpha_to_int(tumor)]['text']
        if 'text' in r:
            return r['text'] + appendix
        if 'title' in r:
            return r['title'] + appendix
        return default


def update_only_add_dict(original: dict, addition: dict):
    new = original.copy()
    for key, new_value in addition.items():
        if key not in original:
            # add
            new[key] = new_value
            continue
        old_value = original[key]
        if old_value == new_value:
            # not update needed
            continue
        raise AssertionError(
            "Expected '%s'='%s', but got '%s' for dict '%s'" % (key, old_value, new_value, original))
    return new


def json_load_and_backup(filename, default=None):
    if default is None:
        default = {}
    if os.path.exists(filename):
        backup_dir = os.path.join(os.path.dirname(filename), 'generated', 'bak')
        if os.path.exists(backup_dir):
            shutil.copy(filename, os.path.join(backup_dir, os.path.basename(filename)))
        else:
            shutil.copy(filename, filename + '.bak')
        return json.load(open(filename))
    return default


def main():
    filename = 'ISO-8-text'

    parser = IsoTextParser('ISO_model/annotations.json')
    parser.load(r'ISO_model/text/%s.txt' % filename)
    if not parser.parse():
        print("Could not parse, some lines were not identified")
        print(parser.missed_lines)
        return

    parser.print()
    parser.write_iso_json(r'ISO_model/generated/%s.json' % filename)
    parser.var_dump_annotations('ISO_model/generated/annotations.json')
    parser.write_work_products('ISO_model/generated/work_products.json')


if __name__ == '__main__':
    main()
