"""
Deprecated
"""
import json
import re

import nltk

# nltk.download('punkt')
# nltk.download('averaged_perceptron_tagger')
# nltk.download('maxent_ne_chunker')
# nltk.download('words')
# nltk.download('treebank')

# Convert to https://en.wikipedia.org/wiki/Object_Constraint_Language
# or http://www.eclipse.org/epsilon/doc/etl/

from ISO_model.scripts.lib.words2num import WordsToNumbers

stemmer = nltk.SnowballStemmer("english")
w2n = WordsToNumbers()


def tokenize(txt: str):
    txt = txt.rstrip('.')
    tokens = nltk.word_tokenize(txt)
    tokens = [t.lower() for t in tokens]
    return {
        'tokens': tokens,
        'original': txt
    }


WORDS3_rx = r'(?:the )?\w+(?: \w+){0,2}'
summation_rx = r'({0}?(?: ?, ?{0})*) and ({0}) ?(?:[,:;]|$)'.format(WORDS3_rx)
r_summation = re.compile(summation_rx)


def extract_summations(spaced_txt):
    ms = r_summation.finditer(spaced_txt)
    if ms:
        summations = []
        for m in ms:
            groups = m.groups()
            summation = [wrd.strip() for wrd in groups[0].split(',')]
            summation += [groups[1]]
            summations.append(summation)
        return summations


class IsoOCLParser:
    # rRel_shall_be_specified = re.compile(r'at least (w+) (.*) shall be specified for each (.*)')
    rCondition = re.compile('if (.*)(?: then (.*)| ?, ?(.*))')
    rRel_shall_be_specified = re.compile(r'(the )?(?:at least (\w*) )?(.*) shall be specified')
    rRel_shall_be_derived = re.compile(r'(the )?(.*) shall be derived from (.*)')
    rRel_shall_be_specified_accordance = re.compile(r'(.*) shall be specified in accordance with (.*)')

    def __init__(self):
        self.output = []

    def parse_el(self):
        if self.el['header']:
            return
        title = tokenize(self.el['title'])
        text = [tokenize(line['text']) for line in self.el.get('text', [])]
        all_text = [title] + text

        if_body = None

        DEBUG_ONLY = (
            # '8.4.2.2',
            # '8.4.2.4', '8.4.2.1',
        )
        if len(DEBUG_ONLY) > 0 and self.el['id'] not in DEBUG_ONLY:
            return

        # print(all_text)
        for t in all_text:
            line = ' '.join(t['tokens'])
            print(t['original'])

            m = IsoOCLParser.rRel_shall_be_specified_accordance.match(line)
            if m:
                print("accordance: %s" % (m.groups(), ))

            m = IsoOCLParser.rCondition.match(line)
            if m:
                if_condition = m.group(1)
                if m.group(2) is None:
                    if_body = m.group(3)
                elif m.group(3) is None:
                    if_body = m.group(2)
                else:
                    print("if failed: %s" % m.groups())
                    if_condition = None

                existence = self.parse_existence(if_body)
                print("if_condition: %s" % if_condition)
                print("if_body: %s\n\t%s" % (if_body, existence))
            else:
                existence = self.parse_existence(line)
                print(existence)

            s = extract_summations(line)
            if s:
                print("%s\nSummations: %s" % (line, s, ))

            raw = t['original']
            tokens = nltk.word_tokenize(raw)
            tagged = nltk.pos_tag(tokens)
            entities = nltk.chunk.ne_chunk(tagged)
            print(entities)

            print()

    def parse_existence(self, text):
        m = IsoOCLParser.rRel_shall_be_specified.match(text)
        if m:
            subject = m.group(3)
            subject = stemmer.stem(subject)
            if m.group(1):
                # Starts with `the`
                return ['>=1', subject]
            if m.group(2):
                at_least = m.group(2)
                n = w2n.parse(at_least)
                return ['>=%d' % n, subject]
            return ['', subject]

    def __call__(self, elements):
        for el in elements:
            self.el = el
            try:
                self.parse_el()
            except Exception as e:
                print("Error on %s" % (self.el, ))
                raise e


if __name__ == '__main__':
    parser = IsoOCLParser()
    parser(json.load(open('ISO_model/part3-text.json')))
