class EolGenerator:
    def __init__(self) -> None:
        self.indent = 0
        self.out = None  # is overwritten in subclass

    def _print(self, line=None, indent_inc=0):
        if line:
            print('\t' * self.indent + line, file=self.out)
        else:
            print(file=self.out)
        self.indent += indent_inc

    def p_close_block(self):
        self.indent -= 1
        self._print('}')

    def p_open_block(self, title):
        self._print(title + ' {', 1)

    def p_block(self, title, fn):
        self.p_open_block(title)
        fn()
        self.p_close_block()

    def _finish(self):
        for i in range(self.indent):
            self.p_close_block()
        self.out.close()

    def p_comment(self, msg: str):
        self._print('// %s' % msg)

    def p_comment_heading(self, header: str):
        N = 80
        self._print('/'*N)
        self._print('// '+(header+' ').ljust(N-3, '/'))
        self._print('/'*N)
