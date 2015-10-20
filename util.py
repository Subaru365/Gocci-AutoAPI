

import sys
import re
import itertools
import collections

def die(m):
    msg(m)
    sys.exit(1)

def msg(m):
    print(m, file=sys.stderr)

def stringify(code):
    return "\"" + code.replace('\\', '\\\\') + "\""

def regexify(code):
    return stringify(code) 
    # return stringify(code.replace('\\', '\\\\')) 

def cAmElCaSe(st):
    return "".join([ s.capitalize() for s in st.split('_') ])

def ident(code):
    res = "    " + code.replace('\n', '\n    ')
    return res[:-4] if res.endswith("    ") else res + "\n"

