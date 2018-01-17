import re
import zipfile
from xml.dom import minidom

import os
from xml.dom.minidom import Node


class DocxToTextParser:
    NS = {
        "wpc": "http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas",
        "mc": "http://schemas.openxmlformats.org/markup-compatibility/2006",
        "o": "urn:schemas-microsoft-com:office:office",
        "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
        "m": "http://schemas.openxmlformats.org/officeDocument/2006/math",
        "v": "urn:schemas-microsoft-com:vml",
        "wp14": "http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing",
        "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
        "w10": "urn:schemas-microsoft-com:office:word",
        "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
        "w14": "http://schemas.microsoft.com/office/word/2010/wordml",
        "w15": "http://schemas.microsoft.com/office/word/2012/wordml",
        "wpg": "http://schemas.microsoft.com/office/word/2010/wordprocessingGroup",
        "wpi": "http://schemas.microsoft.com/office/word/2010/wordprocessingInk",
        "wne": "http://schemas.microsoft.com/office/word/2006/wordml",
        "wps": "http://schemas.microsoft.com/office/word/2010/wordprocessingShape",
    }

    re_table = re.compile(r'table\s+\d+', re.IGNORECASE)
    re_requirement = re.compile(r'\d+(?:\.\d+)+\s+', re.IGNORECASE)

    def __init__(self, start_regex='$^', stop_regex='$^'):
        self.start = re.compile(start_regex) if type(start_regex) is str else start_regex
        self.stop = re.compile(stop_regex) if type(stop_regex) is str else stop_regex
        self.output = []
        self.p = None
        self.table = False
        self.listing_id = None
        self.listing_el = None
        self.ignore_regex = re.compile('^\s*$')

    def parse(self, infile):
        extract_zip(infile)
        document = minidom.parse(os.path.join('tmp', 'word', 'word', 'document.xml'))

        self.table = False
        self.listing_id = None

        # find start
        first = get_by_text_regex(document, 'w:t', self.start, throw_exception=True)

        self.p = get_parent('w:p', first)
        while self.p:
            txt = self._parse_p()

            if txt.startswith('NOTE: Cascading failures are dependent failures'):
                pass

            # See if its good or not
            if self.stop.match(txt):
                break
            if self.ignore_regex.match(txt):
                pass
            else:
                if DocxToTextParser.re_table.match(txt):
                    self.table = True
                if DocxToTextParser.re_requirement.match(txt):
                    self.table = False

                if not self.table:
                    self.output.append(txt)

            self.p = get_next_sibling('w:p', self.p)
        return self.output

    def _parse_p(self):
        listing_id = None
        txt = ''

        # try to find pPr
        pPr = get_child_tag('w:pPr', self.p)
        if pPr:
            numPr = get_child_tag('w:numPr', pPr)
            if numPr:
                ilvl = get_child_tag('w:ilvl', numPr)
                numId = get_child_tag('w:numId', numPr)
                listing_id = get_attr(numId, 'w:val')
        if listing_id:
            # Its a list
            if listing_id == self.listing_id:
                # inc
                self.listing_el = chr(ord(self.listing_el) + 1)
            else:
                # new list
                self.listing_id = listing_id
                self.listing_el = 'a'
            txt = self.listing_el + ') ' + txt

        # concat w:r's
        wr = get_child_tag('w:r', self.p)
        while wr:
            add_txt = self._parse_wr(wr)
            txt += add_txt
            wr = get_next_sibling('w:r', wr)

        return txt

    def _parse_wr(self, wr):
        wt = get_child_tag('w:t', wr)
        if wt:
            return wt.firstChild.nodeValue

        next_tab = get_child_tag('w:tab', wr)
        next_br = get_child_tag('w:br', wr)

        if next_tab or next_br:
            # Tab character, convert to space
            return ' '

        next_drawing = get_child_tag('w:drawing', wr)
        if next_drawing:
            # skip drawings for now
            return ''

        print("missing w:t / w:tab / w:br / w:drawing")
        return ''

    def write(self, outfile):
        with open(outfile, 'w+') as out:
            for l in self.output:
                out.write(l + '\n')


def extract_zip(file):
    zfile = zipfile.ZipFile(file)
    for name in zfile.namelist():
        dirname, filename = os.path.split(name)
        dirname = os.path.join('tmp', dirname)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        zfile.extract(name, dirname)


def get_by_text_regex(element, tag, regex, throw_exception=False):
    for t in element.getElementsByTagName(tag):
        text = t.firstChild.data
        if regex.match(text):
            return t
    if throw_exception:
        for t in element.getElementsByTagName(tag):
            text = t.firstChild.data
            print(text)
        raise AssertionError("`%s` was not found in `%s`" % (regex, element))


def get_next_tag(tag, element, depth=0):
    parent = element.parentNode
    # first go to siblings
    while True:
        element = element.nextSibling
        if element is None:
            break
        sibling_has = get_child_tag_or_self(tag, element)
        if sibling_has:
            return sibling_has
    # check parent
    if parent is None:
        return None
    if parent.nodeName == tag:
        return parent
    return get_next_tag(tag, parent, depth + 1)


def get_child_tag_or_self(tag, element):
    for c in element.childNodes:
        # depth first
        match = get_child_tag_or_self(tag, c)
        if match:
            return match
    if element.nodeName == tag:
        return element
    return None


def get_child_tag(tag, element):
    for c in element.childNodes:
        match = get_child_tag(tag, c)
        if match:
            return match
        if c.nodeName == tag:
            return c
    return None


def get_next_win_parent(tag, element):
    parent = element.parentNode
    if element.nodeName == tag:
        # match
        while True:
            element = element.nextSibling
            if element is None:
                break
            if element.nodeType != Node.ELEMENT_NODE:
                continue
            if element.nodeName == tag:
                return element
            break
    if parent is None:
        return None
    return get_next_win_parent(tag, parent)


def get_next_sibling(tag, element):
    while True:
        element = element.nextSibling
        if element is None:
            return None
        if element.nodeName == tag:
            return element


def get_attr(element, key, default=Node):
    attr = element.attributes.get(key)
    return attr.value if attr else default


def preserve_space(element):
    xml_space = element.attributes.get('xml:space')
    return xml_space is not None and xml_space.value == 'preserve'


def get_parent(tag, element):
    parent = element.parentNode
    if parent is None:
        return None
    if parent.nodeName == tag:
        return parent
    return get_parent(tag, parent)


def main():
    # parser = DocxToTextParser(start_regex=re.compile('1\.\d'), stop_regex='2 Abbreviated terms')
    # parser.parse(r'/home/dennis/Dropbox/0cn/Link to ISO 26262-Draft/ISO_26262-1_DIS_20090813 (Vocabulary).docx')
    # parser.write(r'../part1-text.2.txt')

    start = '7.4 Requirements and recommendations'
    start = '8.3 Inputs to this clause'
    start = '6 Initiation of the safety lifecycle'
    start = 'Item definition\s*$'
    parser = DocxToTextParser(start, stop_regex='Annex')
    parser.parse(r'/home/dennis/Dropbox/0cn/Link to ISO 26262-Draft/ISO_26262-3_DIS_20090813 (Concept phase).docx')
    parser.write(r'../part3-text.2.txt')

    # parser = DocxToTextParser()
    # parser.parse(r'/home/dennis/Dropbox/0cn/Link to ISO 26262-Draft/ISO_26262-4_DIS_20090813 (Product development - system level).docx')
    # parser.write('../part4-text.2.txt')


if __name__ == '__main__':
    main()
