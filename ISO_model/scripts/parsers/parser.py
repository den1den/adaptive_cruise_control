class Parser:
    def load(self, file_name):
        pass

    def parse(self):
        pass

    def validate(self):
        if True:
            raise NotImplementedError()

    @staticmethod
    def _match_replace(s: str, regex, replace: callable):
        pos = 0
        while True:
            m = regex.search(s, pos)
            if m:
                code = replace(m)
                s = s[:m.start()] + code + s[m.end():]
                pos = m.start() + len(code)
            else:
                return s
