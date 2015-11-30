

import tokens
import textwrap
from util import *

def generate(everything):

    res = ""

    uripaths = [(uri.path, uri.normalizedKey()) for uri in everything.uriTokens]
    res += generateUriMasterSwitch(uripaths)

    for uri in everything.uriTokens:
    #     # print(uri.normalizedKey())
    #     # parameterDict = { para.key : {"regex": para.regex, "optional": para.optional } for para in uri.parameters }
    #     parameterDict = [ para.key for para in uri.parameters ]
    #     res += generateParameterCheck(uri.normalizedKey(), parameterDict)

        parameters = [ (para.key, para.regex, para.optional) for para in uri.parameters ]
        res +=generateParameterRegex(parameters)

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

def generateUriMasterSwitch(uripaths):
    res = "switch ($this->uri) {\n"
    for (path, normalized) in uripaths:
        res += "    case 'v3{KEY}':\n".format(KEY=path)
        tmp =  "    $this->getReq_{KEY}();\n".format(KEY=normalized)
        tmp += "    $this->setReq_{KEY}();\n".format(KEY=normalized)
        tmp += "    break;\n"
        res += ident(tmp)

    return res

def generateParameterCheck(uriname, parameters):
    res = "$this->val_param = array(\n"
    for p in parameters:
        res += "    '{KEY}' => Input::get('{KEY}'),\n".format(KEY=p)

    return wrapInVoidFunction("getReq_" + uriname, res + ");\n")

def generateParameterRegex(parameters):
    res = ""

    return wrapInVoidFunction("setReq_" + uriname, parameters())

def wrapInVoidFunction(fname, code):
    res = "private function {FNAME}()\n{{\n{CODE}}}\n".format(FNAME=fname, CODE=ident(code))
    return res

