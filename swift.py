

import types
import textwrap

def generate(tokentree):

    res = "SOURCECODE_LEVEL"
    return SwiftUtil.wrapInClass("API", res)


class SwiftUtil:

    @staticmethod
    def ident(code):
        return "    " + code.replace('\n', '\n    ')

    @staticmethod
    def wrapInClass(classname, code):
        return "class {} {{\n{}\n}}".format(classname, SwiftUtil.ident(code))
     

    

