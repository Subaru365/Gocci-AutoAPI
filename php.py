import tokens
import textwrap
from util import *

def generate(everything):

    test = ""
    res = "<?php\n\n"

    uripaths = [(uri.path, uri.normalizedKey()) for uri in everything.uriTokens]
    # res += generateCodeFunction("GlobalCode", [(e.code, e.msg) for e in everything.globalErrors])


    for uri in everything.uriTokens:

        exclusiveErrors = [ (e.code, e.msg) for e in uri.onlyExclusiveErrors ]

        # res += generateSetRequestParameter(uri.normalizedKey(), uri.parameters)
        res += generateSetResponseParameter(uri.normalizedKey(), uri.responses)

        # res += generateCodeFunction(uri.normalizedKey(), exclusiveErrors)


    return res


def generateCodeFunction(switchname, codes):

    fnc = ''
    for (code, msg) in codes:
        res =  "$this->code = '{CODE}';\n".format(CODE=code)
        res += "$this->message = \"{MSG}\";\n".format(MSG=msg)
        fnc +=  wrapInPublicVoidFunction("set"+switchname+"_"+code, res)

    return fnc


def generateSetRequestParameter(uriname, parameters):

    res = ""
    for p in parameters:

        if not p.optional:
            res += "if(!empty($input_params['{KEY}'])) {{\n\n".format(KEY=p.key)

        res += "if(preg_match('/{REGEX}/', $input_params['{KEY}'])) {{\n".format(REGEX=p.regex, KEY=p.key)
        res += "    $this->req_params['{KEY}'] = $input_params['{KEY}']\n\n".format(KEY=p.key)

        res += "} else {\n"
        res += "    $this->code    = '{CODE}'\n".format(CODE=p.corrospondigMalformError.code)
        res += "    $this->message = \"{MSG}\"\n".format(MSG=p.corrospondigMalformError.msg)
        res += "}\n\n"

        if not p.optional:
            res += "} else {\n"
            res += "    $this->code    = '{CODE}'\n".format(CODE=p.corrospondigMissingError.code)
            res += "    $this->message = \"{MSG}\"\n".format(MSG=p.corrospondigMissingError.msg)
            res += "}\n\n"

    return wrapInPivateFunction("setReqParams"+uriname, res, "$input_params")


def generateSetResponseParameter(uriname, responses):

    def onleaf(leaf):
        nonlocal payload
        payload += "$payload['{KEY}'] = ({TYPE})$res_params['{KEY}'];\n".format(KEY=leaf.key, TYPE=leaf.typ)

    def onarray(array):
        nonlocal payload
        payload += "$payload['{KEY}'] = ({TYPE})$res_params['{KEY}'];\n".format(KEY=array.key, TYPE=array.typ)

    def oncompoundarray(compoundarray):
        nonlocal payload
        tmp = payload
        ref = {}
        payload[compoundarray.key] = [ref]
        payload = ref
        compoundarray.traverse(onleaf, onarray, oncompoundarray, ondict)
        payload = tmp

    def ondict(dictleaf):
        nonlocal payload
        tmp = payload
        payload[dictleaf.key] = {}
        payload = payload[dictleaf.key]
        dictleaf.traverse(onleaf, onarray, oncompoundarray, ondict)
        payload = tmp

    def visitor(root):
        nonlocal payload
        root.traverse(onleaf, onarray, oncompoundarray, ondict)
        begin   = "$res_params = $this->res_params;\n"
        end     = "$this->status['payload'] = $payload;\n"
        payload = "" if payload == "" else wrapInPivateFunction("setRes_" + uriname, begin+payload+end)

    payload = ""
    visitor(responses)
    return payload


def wrapInInterface(cname, code):
    return "interface {NAME} {{\n{CODE}}}\n\n".format(NAME=cname, CODE=ident(code))


def wrapInClass(cname, code):
    return "class {NAME} extends Model\n{{\n{CODE}\n}}\n\n".format(NAME=cname, CODE=ident(code))


def wrapInPublicVoidFunction(fname, code):
    return "public function {NAME}()\n{{\n{CODE}}}\n\n\n".format(NAME=fname, CODE=ident(code))


def wrapInPivateFunction(fname, code, arg=''):
    return "private function {NAME}({ARG})\n{{\n{CODE}}}\n\n\n".format(NAME=fname, CODE=ident(code), ARG=arg)


def originCode():
    return """

    use SingletonTrait;

    private $uri_path;

    private $req_params = array();

    private $status = array(
        'version'   => {VER},
        'uri'       => Uri::string(),
        'code'      => '',
        'message'   => '',
        'payload'   => json_decode('{}'),
    );


    public function getRequest($input_params)
    {        
        $uri  = substr(Uri::string(), 4);
        $this->uri_path     = str_replace("/", "_", $uri);
        $req_function_name  = "setReqParams{$this->uri_path}";

        $this->$req_function_name($input_params);

        return $this->req_params;
    }


    public function setResponse($params)
    {
        $res_function_name = "setPayload{$this->uri_path}";
        
        try {
            $this->$res_function_name($params);
            $this->set_GlobalCode_SUCCESS();
        
        } catch (Excepsion $e){
            error_log($e);
            $this->set_GlobalCode_ERROR_SERVER_SIDE_FAILURE();
        }
    }
"""