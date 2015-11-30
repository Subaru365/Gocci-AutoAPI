

import types
import textwrap
from util import *

def generate(everything):

    res = ""

    for uri in everything.uriTokens:
        # print(uri.normalizedKey())
        # parameterDict = { para.key : {"regex": para.regex, "optional": para.optional } for para in uri.parameters }
        parameterDict = [ para.key for para in uri.parameters ]
        res += generateParameterCheck(uri.normalizedKey(), parameterDict)

        # for par in uri.parameters:
            # print(par)


    # ggg = [ "auth.php": lomgstring1, "get.php": longstring2] 

    return res


            # $this->val_param = array(
                # 'username'           => Input::get('username'),
                # 'os'               => Input::get('os'),
                # 'ver'              => Input::get('ver'),
                # 'model'           => Input::get('model'),
                # 'register_id'     => Input::get('register_id'),
                # );

def generateParameterCheck(uriname, parameters):
    res = "$this->val_param = array(\n" 
    for p in parameters:
        res += "    '{KEY}' => Input::get('{KEY}'),\n".format(KEY=p)
    
    return wrapInVoidFunction("getReq_" + uriname, res + ");\n")

def wrapInVoidFunction(fname, code):
    res = "private function {FNAME}()\n{{\n{CODE}}}\n".format(FNAME=fname, CODE=ident(code))
    return res

