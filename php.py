import tokens
import textwrap
from util import *

def generate(everything):

    tmp = """
<?php
/**
 * Parameter list of uri.
 *
 * @package    Gocci-Mobile
 * @version    4.0.0 (2016/1/21)
 * @author     Subaru365 (a-murata@inase-inc.jp)
 * @copyright  (C) 2015 Akira Murata
 * @link       https://bitbucket.org/inase/gocci-mobile-api
 */

class Model_V4_Param extends Model
{{
    use SingletonTrait;

    public $status = array();

    private $uri_path;

    private $req_params = array();


    private function __construct()
    {{
        $this->status = array(
            'version'   => {VER},
            'uri'       => Uri::string(),
            'code'      => '',
            'message'   => '',
            'payload'   => json_decode('{{}}'),
        );
    }}


    public function getRequest($input_params)
    {{
        $uri  = substr(Uri::string(), 3);
        $this->uri_path     = str_replace("/", "_", $uri);
        $req_function_name  = "setReqParams_".$this->uri_path;

        try {{
            $this->$req_function_name($input_params);
        }}
        catch (Throwable $e){{
            $this->setGlobalCode_ERROR_CLIENT_OUTDATED();
            $json = json_encode(
                $this->status,
                JSON_PRETTY_PRINT|JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES|
                JSON_HEX_TAG|JSON_HEX_AMP|JSON_HEX_QUOT
            );
            echo $json;
            exit;
        }}

        return $this->req_params;
    }}


""".format(VER=everything.version)

    res = ''

    uripaths = [(uri.path, uri.normalizedKey()) for uri in everything.uriTokens]
    res += generateCodeFunction("GlobalCode", [(e.code, e.msg) for e in everything.globalErrors])


    for uri in everything.uriTokens:

        exclusiveErrors = [ (e.code, e.msg) for e in uri.onlyExclusiveErrors ]

        res += generateSetRequestParameter(uri.normalizedKey(), uri.parameters)
        # res += generateSetResponseParameter(uri.normalizedKey(), uri.responses)

        res += generateCodeFunction(uri.normalizedKey(), exclusiveErrors)

    code = tmp + ident(res) + "}\n"

    return code


def generateCodeFunction(fname, codes):

    fnc = ''
    for (code, msg) in codes:
        res =  "$this->status['code']    = '{CODE}';\n".format(CODE=code)
        res += "$this->status['message'] = \"{MSG}\";\n".format(MSG=msg)
        res += "if (!empty($payload)) {\n"
        res += "    $this->status['payload'] = $payload;\n"
        res += "}\n"
        fnc += "public function {NAME}($payload = '')\n{{\n{CODE}}}\n\n\n".format(NAME="set"+fname+"_"+code, CODE=ident(res))

    return fnc


def generateSetRequestParameter(uriname, parameters):

    res = ''
    for p in parameters:

        mid =  "if(!empty($input_params['{KEY}'])) {{\n\n".format(KEY=p.key)
        mid += "    if(preg_match('/{REGEX}/', $input_params['{KEY}'])) {{\n".format(REGEX=p.regex, KEY=p.key)
        mid += "        $this->req_params['{KEY}'] = $input_params['{KEY}'];\n\n".format(KEY=p.key)

        mid += "    } else {\n"
        mid += "        $this->status['code']    = '{CODE}';\n".format(CODE=p.corrospondigMalformError.code)
        mid += "        $this->status['message'] = \"{MSG}\";\n".format(MSG=p.corrospondigMalformError.msg)
        mid += "    }\n\n"

        if not p.optional:
            las = "} else {\n"
            las += "    $this->status['code']    = '{CODE}';\n".format(CODE=p.corrospondigMissingError.code)
            las += "    $this->status['message'] = \"{MSG}\";\n".format(MSG=p.corrospondigMissingError.msg)
            las += "}\n\n"
            res += mid + las
        elif not p.default==None:
            las = "} else {\n"
            las += "    $this->req_params['{KEY}'] = '{DEF}';\n".format(KEY=p.key, DEF=p.default)
            las += "}\n\n"
            res += mid + las
        else:
            res += mid + "}\n\n"

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
        payload += "{KEY}\n".format(KEY=compoundarray.key)
        compoundarray.traverse(onleaf, onarray, oncompoundarray, ondict)

    def ondict(dictleaf):
        nonlocal payload
        payload += "{KEY}\n".format(KEY=dictleaf)
        dictleaf.traverse(onleaf, onarray, oncompoundarray, ondict)

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


# def wrapInPublicVoidFunction(fname, code):
#     return "public function {NAME}()\n{{\n{CODE}}}\n\n\n".format(NAME=fname, CODE=ident(code))


def wrapInPivateFunction(fname, code, arg=''):
    return "private function {NAME}({ARG})\n{{\n{CODE}}}\n\n\n".format(NAME=fname, CODE=ident(code), ARG=arg)
