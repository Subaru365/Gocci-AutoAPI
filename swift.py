

import types
import textwrap

def generate(everything):

    # prepare for Swift

    for uri in everything.uriTokens:
        for para in uri.parameters:
            para.regex = regexify(para.regex)
        for resp in uri.responses:
            resp.regex = regexify(resp.regex)

    allerros = dict()

    for e in everything.globalErrors:
        allerros[e.code] = stringify(e.msg)
    for ut in everything.uriTokens:
        for e in ut.errors:
            allerros[e.code] = stringify(e.msg)

    swift_allErrorsAsEnum = generateEnum("Code", allerros.keys())

    swift_allErrorMessages = generateErrorMsgTable("msgTable", allerros.items())

    # res = swift_allErrorsAsEnum + "\n\n" + swift_allErrorMessages

    paraValiTable = []
    swift_allParameterValidationFunctions = ""
    for uri in everything.uriTokens:
        inner = "class func validateParameter_"+ uri.normalizedKey() +"(map: [String: String]) -> API.Code {\n"
        paraValiTable.append( (uri.path, "validateParameter_"+ uri.normalizedKey()) )
        for para in uri.parameters:
            inner += ident(generateOneParameterRegExCheck("map", para.key, para.regex))
        inner += "\n    return API.Code.SUCCESS\n}\n"
        swift_allParameterValidationFunctions += "\n\n" + inner 

    
    swift_parameterValidationLookUpTable = generateParameterValidationFunctionLookUpTable("parameterValidationLookUpTable", paraValiTable)

    res = ""
    res += swift_allErrorsAsEnum + "\n\n"
    res += swift_allErrorMessages + "\n\n"
    res += swift_parameterValidationLookUpTable + "\n\n"
    res += swift_allParameterValidationFunctions 
    return wrapInClass("API", res)






def stringify(code):
    return "\"" + code.replace('\\', '\\\\') + "\""

def regexify(code):
    return stringify(code.replace('\\', '\\\\')) 


def ident(code):
    return "    " + code.replace('\n', '\n    ')

def wrapInClass(classname, code):
    return "class {} {{\n{}\n}}".format(classname, ident(code))

def generateEnum(enumname, items):
    res = "enum " + enumname + " {"
    for i in items:
        res += "\n    case " + i 
    return res + "\n}"

def generateErrorMsgTable(varname, errorTupels):
    res = "static let "+ varname +": [API.Code: String] = ["
    for k,v in errorTupels:
        res += "\n    API.Code."+ k +": "+ v +","
    return res + "\n]"


def generateParameterValidationFunctionLookUpTable(tablename, uri_functionname_tupels):
    res = "static let "+ tablename +": [String: ([String: String]) -> API.Code] = ["
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
        

