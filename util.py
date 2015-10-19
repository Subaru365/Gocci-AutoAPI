

import sys
import re
import itertools
import collections

def die(m):
    msg(m)
    sys.exit(1)

def msg(m):
    print(m, file=sys.stderr)


class Peekorator(collections.Iterator):
    def __init__(self, it):
        self.it, self.nextit = itertools.tee(iter(it))
        self._advance()
    def _advance(self):
        self.peek = next(self.nextit, None)
    def __next__(self):
        self._advance()
        return next(self.it)

def stringify(code):
    return "\"" + code.replace('\\', '\\\\') + "\""

def regexify(code):
    return stringify(code.replace('\\', '\\\\')) 


def ident(code):
    res = "    " + code.replace('\n', '\n    ')

    if res.endswith("    "):
        return res[:-4]
    else:
        return res + "\n"

