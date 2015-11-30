

import tokens
import textwrap
from util import *

def generate(everything):

    for uri in everything.uriTokens:
        for err in uri.parameter:
            print(err)

    return ""
