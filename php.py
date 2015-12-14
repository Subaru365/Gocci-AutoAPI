import tokens
import textwrap
from util import *

def generate(everything):

    res = "<?php\n\n"

    uripaths = [(uri.path, uri.normalizedKey()) for uri in everything.uriTokens]
    res += generateCodeSwitch("GlobalCode", [(e.code, e.msg) for e in everything.globalErrors])


    for uri in everything.uriTokens:

        res += generateGetReqParamsFunction(uri.normalizedKey())
        parameters = [ (para.key, para.regex, para.optional) for para in uri.parameters ]
        res += generateSetRequestParameter(uri.normalizedKey(), parameters, )
        #res += generateSetResponseParameter(uri.normalizedKey(), uri.responses)
        #res += generateCodeSwitch(uri.normalizedKey(), [ (e.code, e.msg) for e in uri.errors ])

    # ggg = [ "auth.php": lomgstring1, "get.php": longstring2]

    return res


def generateCodeSwitch(switchname, codes):

    fnc = ''

    for (code, msg) in codes:
        res =  "$this->code = '{CODE}';\n".format(CODE=code)
        res += "$this->message = \"{MSG}\";\n".format(MSG=msg)
        fnc +=  wrapInPublicVoidFunction("set"+switchname+"_"+code, res)

    return fnc


def generateGetReqParamsFunction(uripath):

    res  = "$this->setReqParams{KEY}();\n".format(KEY=uripath)
    res += "$this->validationRun();\n"
    res += "return $this->req_params;\n"
    return wrapInPublicVoidFunction("getReqParams"+uripath, res)


def generateSetRequestParameter(uriname, parameters):

    res = "$this->val_params = array(\n"
    for (key, regex, optional) in parameters:
        res += "    '{KEY}' => Input::get('{KEY}'),\n".format(KEY=key)
    res += ");\n\n"

    res += "$val = $this->val;\n"
    res += "$val = Validation::forge('');\n"
    for (key, regex, optional) in parameters:
        res += "$val->add('{KEY}', '{KEY}');\n".format(KEY=key)
        if not optional:
            res += "$val->add_rule('required');\n"
        res += "$val->add_rule('match_pattern', '/{KEY}/');\n\n".format(KEY=regex)
    res += "$this->val = $val;\n"

    return wrapInPivateVoidFunction("setReqParams" + uriname, res)


# def generateSetResponseParameter(uriname, responses):

#     def onleaf(leaf):
#         nonlocal payload
#         payload += "$payload['{KEY}'] = ({TYPE})$res_params['{KEY}'];\n".format(KEY=leaf.key, TYPE=leaf.typ)

#     def visitor(className, root):
#         nonlocal payload
#         root.traverse(onleaf)
#         begin   = "$res_params = $this->res_params;\n"
#         end     = "$this->payload = $payload;\n"
#         payload = "" if payload == "" else wrapInPivateVoidFunction("setRes_" + uriname, begin+payload+end)

#     payload = ""
#     visitor("Payload", responses)
#     return payload


def wrapInInterface(cname, code):
    return "interface {NAME} {{\n{CODE}}}\n\n".format(NAME=cname, CODE=ident(code))

def wrapInClass(cname, code):
    return "class {NAME} extends Model\n{{\n    use SingletonTrait;\n\n{CODE}\n}}\n\n".format(NAME=cname, CODE=ident(code))

def wrapInPublicVoidFunction(fname, code):
    return "public function {NAME}()\n{{\n{CODE}}}\n\n\n".format(NAME=fname, CODE=ident(code))

def wrapInPivateVoidFunction(fname, code):
    return "private function {NAME}()\n{{\n{CODE}}}\n\n\n".format(NAME=fname, CODE=ident(code))

