# converts a .txt file of ISO document to an json file
import json
import sys
import re


class ParseText:
    title_regex = re.compile(r'^(\d{1,3}(?:\.\d{1,3}){1,5})\s*(.*)$')
    NOTE_regex = re.compile(r'^\s*NOTE\s*(.*)$')
    SUMMATION_ordered_regex = re.compile(r'^\s*([a-z0-9]+)\)\s*(.*)$')
    SUMMATION_unordered_regex = re.compile(r'^\s*⎯\s*(.*)$')
    EXAMPLE_regex = re.compile(r'^\s*EXAMPLE\s*(?:\d+\s*)?(.*)$')
    ANNOTATION_HEADER_regex = re.compile(r'^([A-Z]+)>(.*)$')

    def __init__(self):
        self.output = []

    def __call__(self, lines):
        self.prev_line = None
        self.curr_line = None
        self.element = None
        self.curr_SUM = None
        self.curr_ordered_SUM = None

        self.missed_lines = []

        no = 0
        for line in lines:

            # Parse annotation
            annotation = ''
            m = ParseText.ANNOTATION_HEADER_regex.match(line)
            if m is not None:
                annotation = m.group(1)
                line = m.group(2)

            no += 1
            self.prev_line = self.curr_line
            self.curr_line = {
                'text': line,
                'line_no': no,
            }

            m = ParseText.title_regex.match(line)
            if m is not None:
                # write previous element
                if self.element is not None:
                    if len(self.missed_lines) > 0:
                        self.element['text'] = self.missed_lines
                        self.missed_lines = []

                    ignore = self.element.pop('ignore')
                    if not ignore:
                        self.output.append(self.element)

                # prepare next
                self.element = {
                    'id': m.group(1),
                    'title': m.group(2).strip(),
                    'line_no': no,
                    'header': 'H' in annotation,
                    'ignore': 'I' in annotation,
                }

                self.curr_SUM = None
                self.curr_ordered_SUM = None
                continue

            m = ParseText.NOTE_regex.match(line)
            if m is not None:
                self.element.setdefault('notes', [])
                self.element['notes'] += [m.group(1)]
                continue

            m = ParseText.SUMMATION_ordered_regex.match(line)
            if m is not None:
                if self.curr_ordered_SUM is None:
                    # start new summation
                    self.curr_ordered_SUM = {
                        'title': self.prev_line,
                        'elements': [],
                        'ordered': True,
                    }
                    self.element.setdefault('sums', [])
                    self.element['sums'] += [self.curr_ordered_SUM]

                    if not ParseText.title_regex.match(self.prev_line['text']):
                        self.missed_lines.pop()

                self.curr_ordered_SUM['elements'] += [{
                    'index': m.group(1),
                    'text': m.group(2),
                    'line_no': no,
                }]
                continue
            else:
                self.curr_ordered_SUM = None

            m = ParseText.SUMMATION_unordered_regex.match(line)
            if m is not None:
                if self.curr_SUM is None:
                    # start new summation
                    self.curr_SUM = {
                        'title': self.prev_line,
                        'elements': [],
                        'ordered': False,
                    }
                    self.element.setdefault('sums', [])
                    self.element['sums'] += [self.curr_SUM]

                    if not ParseText.title_regex.match(self.prev_line['text']):
                        self.missed_lines.pop()

                self.curr_SUM['elements'] += [{
                    'text': m.group(1),
                    'line_no': no,
                }]
                continue
            else:
                self.curr_SUM = None

            m = ParseText.EXAMPLE_regex.match(line)
            if m is not None:
                self.element.setdefault('examples', [])
                self.element['examples'] += [m.group(1)]
                continue

            self.missed_lines.append(self.curr_line)

        return len(self.missed_lines) == 0

    def save(self, out_filename):
        if len(self.missed_lines) > 0:
            raise Exception("Parsing failed")
        json.dump(self.output, open(out_filename, 'w+'), indent=2)


if __name__ == '__main__':
    in_file = sys.argv[1]
    out_file = sys.argv[2]

    parser = ParseText()
    if not parser(open(in_file, 'r')):
        print("Could not parse, some lines were not identified")
        print(parser.missed_lines)
    else:
        parser.save(out_file)
