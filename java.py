import tokens
from util import *


def generate(everything):
    for uri in everything.uriTokens:
        for para in uri.parameters:
            para.regex = regexify(para.regex)

    java_intro = staticFinalString("baseurl", stringify(everything.apidict.pairs["baseurl"]))
    java_intro += staticFinalString("testurl", stringify(everything.apidict.pairs["testurl"]))

    globalCode = "GlobalCode"

    java_globalHashMap = staticFinalHashMap(globalCode)

    java_allErrorsAsEnum = generateEnum(globalCode, [e.code for e in everything.globalErrors])

    tmp = {e.code: stringify(e.msg) for e in everything.globalErrors}
    java_allErrorMessages = generateErrorMsgTable(globalCode, tmp)

    tmp = {e.code: e.code for e in everything.globalErrors}
    java_codeReverseLookUpTable = generateCodeReverseLookUpTable(globalCode, tmp)

    uriTree = everything.transformURITokensFromFlatArrayToTreeStructureBasedOnTheirPath()

    def onURIToken(uri):
        localCode = uri.path.replace('/', "") + "LocalCode"

        res = staticFinalHashMap(localCode) + "\n"
        res += generateEnum(localCode, [e.code for e in uri.errors]) + "\n"

        tmp = {e.code: stringify(e.msg) for e in uri.errors}
        res += generateErrorMsgTable(localCode, tmp) + "\n"

        tmp = {e.code: e.code for e in uri.errors}
        res += generateCodeReverseLookUpTable(localCode, tmp) + "\n"

        return res

    def subClassBuilder(eda):
        classet = ""
        for node, v in eda.items():
            if type(v) is dict:
                classet += ident(subClassBuilder(v)) + "\n"
            elif type(v) is tokens.URIToken:
                classet += onURIToken(v) + "\n"
        return classet

    java_subClasses = subClassBuilder(uriTree)

    # def sortarray(ar):
    # allcodes = list(ar.keys())
    # allcodes.sort(reverse=True)

    res = java_intro + "\n"
    res += java_globalHashMap + "\n"
    res += java_allErrorsAsEnum + "\n"
    res += java_codeReverseLookUpTable + "\n"
    res += java_allErrorMessages + "\n"
    res += java_subClasses + "\n"

    return "package com.inase.android.gocci.datasource.api;\n\nimport java.util.Map;\nimport java.util.concurrent.ConcurrentHashMap;\n\n" + wrapInClass(
        "Util", res)


def staticFinalString(varname, value):
    return "private static final String {vn} = {v};\n".format(vn=varname, v=value)


def staticFinalHashMap(localcode):
    return "private static final ConcurrentHashMap<{lc}, String> {v} = new ConcurrentHashMap<>();\n" \
           "private static final ConcurrentHashMap<String, {lc}> {v2} = new ConcurrentHashMap<>();\n".format(
        lc=localcode,
        v=localcode + "Map",
        v2=localcode + "ReverseMap")


def generateParameterGetter(APIName, path, parameters):
    res = "public static String get" + APIName + "(".join(["String " + x.key + ", " for x in parameters]) + ") {\n"
    return res + "return testurl + let parameters = InternalParameterClass()\n"


def wrapInInterface(classname, code):
    return "interface {NAME} {{\n{CODE}}}\n".format(NAME=classname, CODE=ident(code))


def wrapInClass(classname, code):
    return "public class {NAME} {{\n{CODE}}}\n".format(NAME=classname, CODE=ident(code))


def generateEnum(enumname, items):
    res = "public enum " + enumname + " {"
    for i in items:
        res += "\n  " + i + ","
    return res + "\n}"


def generateErrorMsgTable(localCode, errorMsgDict):
    res = "public static String " + localCode + "MessageTable(" + localCode + " code) {\n\tif(" + localCode + "Map.isEmpty()) {"
    for k, v in errorMsgDict.items():
        res += "\n\t\t" + localCode + "Map.put(" + localCode + "." + k + ", " + v + ");"
    res += "\n\t}\n\t\tString message = null;\n\t\tfor(Map.Entry<" + localCode + ", String> entry : " + localCode + "Map.entrySet()) {\n\t\t\t" \
                                                                                                                    "if(entry.getKey().equals(code)) {\n\t\t\t\tmessage = entry.getValue();\n\t\t\t\tbreak;\n}\n}\nreturn message;\n}"
    return res


def generateCodeReverseLookUpTable(localCode, codes):
    res = "public static " + localCode + " " + localCode + "ReverseLookupTable(String message) {\n\tif(" + localCode + "ReverseMap.isEmpty()) {"
    for c in codes:
        res += "\n\t\t" + localCode + "ReverseMap.put(" + stringify(c) + ", " + localCode + "." + c + ");"
    res += "\n\t}\n\t\t" + localCode + " code = null;\n\t\tfor(Map.Entry<String, " + localCode + "> entry : " + localCode + "ReverseMap.entrySet()) {\n\t\t\t" \
                                                                                                                            "if(entry.getKey().equals(message)) {\n\t\t\t\tcode = entry.getValue();\n\t\t\t\tbreak;\n}\n}\nreturn code;\n}"
    return res
