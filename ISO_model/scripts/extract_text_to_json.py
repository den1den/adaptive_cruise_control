# converts a .txt file of ISO document to an json file
import json
import os
import shutil
import sys
import re
from jsonschema import validate as json_scheme_validate

from ISO_model.schemes.simple_model_inst_list_scheme import ModelInstanceIdList
from ISO_model.schemes.work_product_scheme import WorkProduct


def str_rev(string: str):
    return ''.join(reversed(string))


class SimpleTextToJsonParser:
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
        self.output = {}
        self.annotations = json.load(open(read_from_annotations_file)) if read_from_annotations_file else {}
        self.work_products = {}  # Is not an input for this parser
        self.prev_line = None
        self.curr_line = None
        self.element = None
        self.missed_lines = []
        self.curr_SUM = None
        self.curr_ordered_SUM = None
        self.id_prefix = ''
        self.next_is_wp = False

    def parse_file(self, text_file):
        return self.parse(
            [l for l in open(text_file, 'r')],
            re.match('.*part-?(\d+).*', text_file).group(1) + '-'
        )

    def parse(self, lines, id_prefix):
        self.id_prefix = id_prefix
        self.curr_line = None
        self.element = None

        self.missed_lines = []

        no = 0
        for line in lines:
            no += 1
            self.prev_line = self.curr_line
            self.curr_line = {
                'text': line,
                'line_no': no,
            }
            self.parse_line()
        return len(self.missed_lines) == 0

    def parse_line(self):
        line_number = self.curr_line['line_no']
        text, annotation = self.parse_annotations(self.curr_line['text'])

        m = SimpleTextToJsonParser.re_title.match(text)
        if m:
            # Requirement header found
            if self.element:
                # write previous element
                if len(self.missed_lines) > 0:
                    self.element['text'] = self.missed_lines
                    self.missed_lines = []

            # prepare next
            rid = self.id_prefix + m.group(1)
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
        m = SimpleTextToJsonParser.re_note.match(text)
        if m:
            self.element.setdefault('notes', [])
            self.element['notes'] += [m.group(1)]
            return

        # search summation
        m = SimpleTextToJsonParser.re_ordered_summation.match(text)
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

        m = SimpleTextToJsonParser.re_unordered_summation.match(text)
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

                if not SimpleTextToJsonParser.re_title.match(self.prev_line['text']):
                    self.missed_lines.pop()

            self.curr_SUM['elements'] += [{
                'text': m.group(1),
                'line_no': line_number,
            }]
            return
        else:
            self.curr_SUM = None

        # search example
        m = SimpleTextToJsonParser.re_example.match(text)
        if m:
            self.element.setdefault('examples', [])
            self.element['examples'] += [m.group(1)]
            return

        self.missed_lines.append(self.curr_line)

    def parse_work_product(self):
        title = self.element['title']
        rid = self.element['id']
        ann_work_product = self.annotations[rid].get('work_product', False)
        m = SimpleTextToJsonParser.re_work_product.match(title)
        if ann_work_product or m:
            if not m:
                raise AssertionError(
                    "Work product fail '%s' to %s" % (title, SimpleTextToJsonParser.re_work_product))
            work_product_name = m.group(1)
            work_product_range = m.group(2)

            WP = {
                'name': work_product_name,
                'based_on': work_product_range,
            }

            while True:
                rm = SimpleTextToJsonParser.re_simple_req_range.match(work_product_range)
                if rm:
                    base = rm.group(1)
                    WP['based_on__refs_to_id'] = 'IsoRequirement'
                    WP['based_on'] = [self.id_prefix + '%s.%d' % (base, digit) for digit in
                                          range(int(rm.group(2)), int(rm.group(3)))]
                    break
                rm = SimpleTextToJsonParser.re_simple_req_summation_rev.match(str_rev(work_product_range))
                if rm:
                    WP['based_on__refs_to_id'] = 'IsoRequirement'
                    WP['based_on'] = [self.id_prefix + str_rev(r) for r in reversed(rm.groups())]
                    break
                rm = SimpleTextToJsonParser.re_requirement_ref.match(work_product_range)
                if rm:
                    WP['based_on__refs_to_id'] = 'IsoRequirement'
                    WP['based_on'] = [self.id_prefix + rm.group(1)]
                    break
                break

            self.work_products[rid] = WP

    boolean_annotations = {
        'I': 'ignore',
        'H': 'header',
        'W': 'work_product',
    }

    def parse_annotations(self, line):
        m = SimpleTextToJsonParser.re_annotation.match(line)
        annotation = {}
        if m:
            annotation_str = m.group(1)
            for char in annotation_str:
                if char in SimpleTextToJsonParser.boolean_annotations:
                    annotation[SimpleTextToJsonParser.boolean_annotations[char]] = True
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

    def write(self, out_filename):
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
        for r in self.output.values():
            print("%s\t%d\t%s" % (str(r['id']).ljust(10), int(r['line_no']), r['title']))

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



def dict_update(ori: dict, update):
    ori.update(update)
    return ori


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
    parser = SimpleTextToJsonParser('ISO_model/annotations.json')
    if not parser.parse_file(r'ISO_model/part3-text.2.txt'):
        print("Could not parse, some lines were not identified")
        print(parser.missed_lines)
    else:
        # parser.print()
        parser.write(r'ISO_model/generated/part3-text.2.json')
        parser.var_dump_annotations('ISO_model/generated/annotations.json')
        parser.write_work_products('ISO_model/generated/work_products.json')


if __name__ == '__main__':
    main()
