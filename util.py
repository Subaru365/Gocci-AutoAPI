

import sys
import re

def die(m):
    msg(m)
    sys.exit(1)

def msg(m):
    print(m, file=sys.stderr)

def filterForLinesStartingWith(dirtyContend, filterRegEx):
    res = []
    for line in dirtyContend:
        if re.match(filterRegEx, line):
            res.append(line.strip())
    return res
