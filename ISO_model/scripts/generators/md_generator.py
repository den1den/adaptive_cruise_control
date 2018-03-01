from datetime import datetime


class MdGenerator:
    def __init__(self, out) -> None:
        self.indent = ''
        self.out = out
        print('<!-- Generated at %s -->\n' % datetime.now(), file=self.out)

    def _print(self, text):
        print(self.indent + (' ' if len(self.indent) > 0 else '') + text, file=self.out)

    def h(self, text: str, n=1):
        self._print('#' * n + ' ' + text)

    def single_table(self, d: dict, keys=None):
        if keys is None:
            keys = sorted(d.keys())
        self._table_row(keys)
        self._table_row((':---' for i in range(len(keys))))
        self._table_row(('%s' % d.get(k, '-') for k in keys))
        self.br()

    def _table_row(self, values):
        self._print('|' + ' | '.join(values) + '|')

    def open_quote(self):
        self.indent += '>'

    def close_quote(self):
        self.indent = self.indent.rstrip('>')

    def p(self, text):
        for l in text.split('\n'):
            self._print(l)
        self.br()

    def br(self):
        self._print('')

    def new_line(self):
        print(file=self.out)

    def close(self):
        self.out.flush()

