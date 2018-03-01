from functools import total_ordering
from json import JSONEncoder

import sys

ASILS = (
    ('D', 'D'),
    ('C', 'C'),
    ('B', 'B'),
    ('A', 'a'),
    ('QM', 'qm', ''),
)


@total_ordering
class Asil:
    def __init__(self, obj):
        if obj is None:
            raise Exception()
        if type(obj) is Asil:
            self.asil = obj.asil
            return
        for n, ASIL in enumerate(iter(ASILS)):
            if obj in ASIL:
                self.asil = n
                return
        print("Could not detect ASIL value: %s" % obj, file=sys.stderr)
        self.asil = len(ASILS) - 1

    def __eq__(self, o: object) -> bool:
        return isinstance(o, Asil) and self.asil == o.asil

    def __lt__(self, other):
        return self.asil > other.asil

    def __str__(self):
        return ASILS[self.asil][0]

    def __repr__(self):
        return self.__str__()

    class JsonEncoder(JSONEncoder):
        def default(self, o):
            if type(o) is Asil:
                return str(o)
            return super().default(o)