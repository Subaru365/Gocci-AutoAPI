

import types
import textwrap
from util import *

def generate(everything):


    def forEachLeaf(resp):
        resp.regex = regexify(resp.regex)

    for uri in everything.uriTokens:
        for para in uri.parameters:
            para.regex = regexify(para.regex)
        uri.responses.recursive_traverse(forEachLeaf, lambda x:x)

    swift_intro  = staticLetString("baseurl", everything.apidict.pairs["baseurl"])
    swift_intro += staticLetString("testurl", everything.apidict.pairs["testurl"])

    swift_allErrorsAsEnum = generateEnum("GlobalCode", [ e.code for e in everything.globalErrors ] )

    tmp = { e.code: stringify(e.msg) for e in everything.globalErrors }
    swift_allErrorMessages = generateErrorMsgTable("globalErrorMessageTable", tmp)


    tmp = { e.code: e.code for e in everything.globalErrors }
    swift_codeReverseLookUpTable = generateCodeReverseLookUpTable("globalErrorReverseLookupTable", tmp)

    swift_APIClassOtherStuff = """
        static var globalErrorMapping: [GlobalCode: (GlobalCode, String)->()] = [:]
        static var onUnhandledError: (GlobalCode, String)->() = API2.unhandledErrorDefault

        private class func unhandledErrorDefault(c: GlobalCode, m: String) {
            print("FATAL: UNHANDLED API ERROR: \(c): \(m)")
        }

        class func on(gcode: GlobalCode, perform:(GlobalCode, String)->()) {
            globalErrorMapping[gcode] = perform
        }"""

    swift_handyGlobalErrorOns = generateHandyGloabalErrorOn([ e.code for e in everything.globalErrors ])

    uriTree = everything.transformURITokensFromFlatArrayToTreeStructureBasedOnTheirPath()


    def beforeNode(node, nodeName):
        return "class " + nodeName + "{\n\n"

    def afterNode(node, nodeName):
        return "}\n\n" 

    def onURIToken(uri, nodeName):
        return "let apipath = " + stringify(uri.path)

    def classBuilder(eda): 
        classet = ""
        for node, v in eda.items():
            if type(v) is dict:
                clas  = beforeNode(v, node)
                clas += ident(classBuilder(v))
                clas += afterNode(v, node)
                classet += clas
            elif type(v) is types.URIToken:
                classet += wrapInClass(node, onURIToken(v, node)) + "\n\n"
        return classet

    print(classBuilder(uriTree))
    return ""


    # allcodes = list(allerros.keys())
    # allcodes.sort(reverse=True)

    # paraValiTable = []
    # swift_allParameterValidationFunctions = ""
    # for uri in everything.uriTokens:
        # inner = "class func validateParameter_"+ uri.normalizedKey() +"(map: [String: String]) -> API.Code {\n"
        # paraValiTable.append( (uri.path, "validateParameter_"+ uri.normalizedKey()) )
        # for para in uri.parameters:
            # inner += ident(generateOneParameterRegExCheck("map", para.key, para.regex))
        # inner += "\n    return API.Code.SUCCESS\n}\n"
        # swift_allParameterValidationFunctions += "\n\n" + inner 

    
    # swift_parameterValidationLookUpTable = generateParameterValidationFunctionLookUpTable("parameterValidationLookUpTable", paraValiTable)

    res = swift_intro + "\n\n"
    res += swift_allErrorsAsEnum + "\n\n"
    res += swift_codeReverseLookUpTable + "\n\n"
    res += swift_allErrorMessages + "\n\n"
    res += swift_handyGlobalErrorOns + "\n\n"
    # res += swift_parameterValidationLookUpTable + "\n\n"
    # res += swift_allParameterValidationFunctions 

    return wrapInClass("API2", res)





def staticLetString(varname, value):
    return "static let {vn} = {v}\n".format(vn=varname, v=value)


def wrapInClass(classname, code):
    return "class {} {{\n{}\n}}".format(classname, ident(code))

def generateEnum(enumname, items):
    res = "enum " + enumname + " {"
    for i in items:
        res += "\n    case " + i 
    return res + "\n}"

def generateErrorMsgTable(varname, errorMsgDict):
    res = "static let "+ varname +": [GlobalCode: String] = ["
    for k,v in errorMsgDict.items():
        res += "\n    ."+ k +": \n\t\t"+ v +","
    return res + "\n]"

def generateCodeReverseLookUpTable(varname, codes):
    res = "static let "+ varname +": [String: GlobalCode] = ["
    for c in codes:
        res += "\n    "+ stringify(c) +": ."+ c +","
    return res + "\n]"

def generateHandyGloabalErrorOn(ecodes):
    template = """
class func on_{ec}(perform:(GlobalCode, String)->()) {{
    globalErrorMapping[.{ec}] = perform\n}}"""
    return "".join( [ template.format(ec=ec) for ec in ecodes ] )

def generateParameterValidationFunctionLookUpTable(tablename, uri_functionname_tupels):
    res = "static let "+ tablename +": [String: ([String: String]) -> GlobalCode] = ["
    for k,v in uri_functionname_tupels:
        res += "\n    " + stringify(k) + ": API."+ v +","
    return res + "\n]"


def generateOneParameterRegExCheck(tablename, parameter, regex):
    return  """
if let value = {MAPNAME}["{PARAMETER}"] {{
    if !APIUtil.matches(value, re: {REGEX}) {{
        return API.Code.ERROR_PARAMETER_{PARAMETERUPCASE}_MALFORMED
    }}
}}
else {{
    return API.Code.ERROR_PARAMETER_{PARAMETERUPCASE}_MISSING
}}
""".format(MAPNAME=tablename, PARAMETER=parameter, REGEX=regex, PARAMETERUPCASE=parameter.upper())
        




    # def pretty(d, indent=0):
        # for key, value in d.items():
            # print('\t' * indent + str(key))
            # if isinstance(value, dict):
                # pretty(value, indent+1)
            # else:
                # print( '\t' * (indent+1) + str(value.path))
