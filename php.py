

import tokens
import textwrap
from util import *

def generate(everything):

    res = "<?php\n"

    uripaths = [(uri.path, uri.normalizedKey()) for uri in everything.uriTokens]
    res += generateUriRequestSwitch(uripaths)
    res += generateUriResponseSwitch(uripaths, uri.responses)

    for uri in everything.uriTokens:

        parameters = [ (para.key, para.regex, para.optional) for para in uri.parameters ]
        res += generateSetRequestParameter(uri.normalizedKey(), parameters)

        res += generatePayloadType(uri.normalizedKey(), uri.responses)


    # ggg = [ "auth.php": lomgstring1, "get.php": longstring2]

    return res


def generateUriRequestSwitch(uripaths):
    res = "switch ($this->uri)\n{\n"
    for (path, normalized) in uripaths:
        res += "case 'v3{KEY}':\n".format(KEY=path)
        tmp =  "    $this->getReq_{KEY}();\n".format(KEY=normalized)
        tmp += "    $this->setReq_{KEY}();\n".format(KEY=normalized)
        tmp += "    break;\n\n"
        res += ident(tmp)
    res += "default:\n"
    res += "    Model_V3_Status::getStatus();\n"
    res += "    break;\n}\n"

    return wrapInVoidFunction("setRequestParameter", res)


def generateUriResponseSwitch(uripaths, responses):

    def onleaf(leaf):
        nonlocal payload
        payload += "1"

    def visitor(className, root):
        nonlocal payload
        root.traverse(onleaf)
        begin   = "$res_params = $this->res_params;\n"
        end     = "$this->payload = $payload;\n"

    payload = ""
    visitor("Payload", responses)

    begin = "switch ($this->uri)\n{\n"
    for (path, normalized) in uripaths:
        payload = ""
        visitor("Payload", responses)


        res += "case 'v3{KEY}':\n".format(KEY=path)
        tmp =  "    $this->getReq_{KEY}();\n".format(KEY=normalized)
        tmp += "    $this->setReq_{KEY}();\n".format(KEY=normalized)
        tmp += "    break;\n\n"
        res += ident(tmp)
    end += "default:\n"
    end += "    Model_V3_Status::getStatus();\n"
    end += "    break;\n}\n"

    res = "" if payload == "" else wrapInVoidFunction("setRes_" + uriname, begin+payload+end)
    return wrapInVoidFunction("setRequestParameter", res)


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

    return wrapInVoidFunction("setReq_" + uriname, res)


def generatePayloadType(uriname, responses):

    def onleaf(leaf):
        nonlocal payload
        payload += "$payload['{KEY}'] => ({TYPE})$res_params['{KEY}'];\n".format(KEY=leaf.key, TYPE=leaf.typ)

        # payload += "$val = $this->val;\n"
        # payload += "$val->add('{KEY}', '{KEY}');\n".format(KEY=leaf.key)
        # payload += "$val->add_rule('match_pattern', '/{KEY}/');\n".format(KEY=leaf.regex)
        # payload += "$this->val = $val;\n\n"

    # def onarray(array, typ="[String] = []"):
    #     nonlocal payload
    #     payload += "var {VARNAME}: {TYPE}\n".format(VARNAME=array.key, TYPE=typ)

    # def oncompoundarray(compoundarray):
    #     # oncomplextype(compoundarray, "[[String: {CLASSNAME}!]] = []", onarray)
    #     oncomplextype(compoundarray, "[{CLASSNAME}] = []", onarray)

    # def ondict(dictleaf):
    #     # oncomplextype(dictleaf, "[String: {CLASSNAME}!] = [:]", onleaf)
    #     oncomplextype(dictleaf, "{CLASSNAME} = {CLASSNAME}()", onleaf)

    # def oncomplextype(complextype, typestr, typegenerator):
    #     # This is magic^^
    #     nonlocal payload
    #     payload += "\n"
    #     clas = cAmElCaSe(complextype.key)
    #     typegenerator(complextype, typestr.format(CLASSNAME=clas))
    #     tmp = payload
    #     payload = ""
    #     visitor(clas, complextype)
    #     payload = tmp + payload

    def visitor(className, root):
        nonlocal payload
        root.traverse(onleaf)
        begin   = "$res_params = $this->res_params;\n"
        end     = "$this->payload = $payload;\n"
        payload = "" if payload == "" else wrapInVoidFunction("setRes_" + uriname, begin+payload+end)

    payload = ""
    visitor("Payload", responses)
    return payload


def wrapInVoidFunction(fname, code):
    res = "private function {FNAME}()\n{{\n{CODE}}}\n\n".format(FNAME=fname, CODE=ident(code))
    return res

