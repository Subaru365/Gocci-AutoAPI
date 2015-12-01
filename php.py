

import tokens
import textwrap
from util import *

def generate(everything):

    res = "<?php\n\n"

    uripaths = [(uri.path, uri.normalizedKey()) for uri in everything.uriTokens]
    # res += generateUriRequestSwitch(uripaths)

    # res += generateGlobalCodeSwitch("GlobalCode", [e.code for e in everything.globalErrors])


    for uri in everything.uriTokens:

        parameters = [ (para.key, para.regex, para.optional) for para in uri.parameters ]
        res += generateSetRequestParameter(uri.normalizedKey(), parameters)
        res += generateSetResponseParameter(uri.normalizedKey(), uri.responses)



    # ggg = [ "auth.php": lomgstring1, "get.php": longstring2]

    return res


def generateUriRequestSwitch(uripaths):

    res = "switch ($this->uri)\n{\n"

    for (path, normalized) in uripaths:
        res += "case 'v3{KEY}':\n".format(KEY=path)
        res += "    $this->setReq_{KEY}();\n".format(KEY=normalized)
        res += "    break;\n\n"

    res += "default:\n"
    res += "    Model_V3_Status::getStatus();\n"
    res += "    break;\n}\n"

    return wrapInPivateVoidFunction("setRequestParameter", res)


def generateSetRequestParameter(uriname, parameters):

    res = "$this->val_params = array(\n"
    for (key, regex, optional) in parameters:
        res += "    '{KEY}' => Input::get('{KEY}'),\n".format(KEY=key)
    res += ");\n\n"

    res += "$val = $this->val;\n"
    for (key, regex, optional) in parameters:
        res += "$val->add('{KEY}', '{KEY}');\n".format(KEY=key)
        res += "$val->add_rule('match_pattern', '/{KEY}/');\n".format(KEY=regex)
        if not optional:
            res += "$val->add_rule('required');\n"
    res += "$this->val = $val;\n"

    return wrapInPivateVoidFunction("setReq_" + uriname, res)


def generateSetResponseParameter(uriname, responses):

    def onleaf(leaf):
        nonlocal payload
        payload += "$payload['{KEY}'] => ({TYPE})$res_params['{KEY}'];\n".format(KEY=leaf.key, TYPE=leaf.typ)

    def visitor(className, root):
        nonlocal payload
        root.traverse(onleaf)
        begin   = "$res_params = $this->res_params;\n"
        end     = "$this->payload = $payload;\n"
        payload = "" if payload == "" else wrapInPivateVoidFunction("setRes_" + uriname, begin+payload+end)

    payload = ""
    visitor("Payload", responses)
    return payload


def wrapInInterface(cname, code):
    return "interface {NAME} {{\n{CODE}}}\n\n".format(NAME=cname, CODE=ident(code))


def wrapInClass(cname, code):
    return "class {NAME} {{\n{CODE}}}\n\n".format(NAME=cname, CODE=ident(code))


def wrapInPivateVoidFunction(fname, code):
    return "private function {NAME}()\n{{\n{CODE}}}\n\n".format(NAME=fname, CODE=ident(code))

