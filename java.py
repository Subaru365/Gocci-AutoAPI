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

    def onURITable(uri):
        localCode = uri.path.title().replace('/', "") + "LocalCode"

        res = staticFinalHashMap(localCode) + "\n"

        res += generateGetAPI(uri.path, uri.parameters) + "\n\n"

        res += generateEnum(localCode, [e.code for e in uri.errors]) + "\n\n"

        tmp = {e.code: stringify(e.msg) for e in uri.errors}
        res += generateErrorMsgTable(localCode, tmp) + "\n\n"

        tmp = {e.code: e.code for e in uri.errors}
        res += generateCodeReverseLookUpTable(localCode, tmp) + "\n\n"

        return res

    def utilLocalCodeBuilder(eda):
        classet = ""
        for node, v in eda.items():
            if type(v) is dict:
                classet += ident(utilLocalCodeBuilder(v))
            elif type(v) is tokens.URIToken:
                classet += onURITable(v)
        return classet

    java_subClasses = utilLocalCodeBuilder(uriTree)

    def onURIRegex(uri):

        res = generateParameterRegexInInterface(uri.path, uri.parameters) + "\n\n"
        res += generateResponseRegexInInterface(uri.path, uri.parameters) + "\n\n"
        res += generateResponseInInterface(uri.path) + "\n\n"
        res += generateResponseCallbackInInterface(uri.path) + "\n"

        return res

    def utilRegexBuilder(eda):
        classet = ""
        for node, v in eda.items():
            if type(v) is dict:
                classet += utilRegexBuilder(v)
            elif type(v) is tokens.URIToken:
                classet += onURIRegex(v)
        return classet

    java_regexInterface = utilRegexBuilder(uriTree)

    res = java_intro + "\n"
    res += java_globalHashMap + "\n"
    res += java_allErrorsAsEnum + "\n"
    res += java_codeReverseLookUpTable + "\n"
    res += java_allErrorMessages + "\n"
    res += java_subClasses

    util = wrapInClass("Util", res)

    res2 = "Util.GlobalCode check_global_error();\n"
    res2 += java_regexInterface + "\n"
    res2 += util + "\n"

    def onURIImpl(uri):

        res = generateParameterRegexInImpl(uri.path, uri.parameters) + "\n\n"
        res += generateResponseRegexInImpl(uri.path, uri.parameters) + "\n\n"
        res += generateResponseInImpl(uri.path) + "\n\n"

        return res

    def implRegexBuilder(eda):
        classet = ""
        for node, v in eda.items():
            if type(v) is dict:
                classet += implRegexBuilder(v)
            elif type(v) is tokens.URIToken:
                classet += onURIImpl(v)
        return classet

    java_regexImpl = implRegexBuilder(uriTree)
    java_regexImpl += """@Override
        public Util.GlobalCode check_global_error() {
            if (com.inase.android.gocci.utils.Util.getConnectedState(Application_Gocci.getInstance().getApplicationContext()) == com.inase.android.gocci.utils.Util.NetworkStatus.OFF) {
                return Util.GlobalCode.ERROR_NO_INTERNET_CONNECTION;
            }
            return Util.GlobalCode.SUCCESS;
        }"""

    res2 += implClassWithImpl(java_regexImpl)

    return """package com.inase.android.gocci.datasource.api;

import com.inase.android.gocci.Application_Gocci;
import com.inase.android.gocci.domain.model.HeaderData;
import com.inase.android.gocci.domain.model.ListGetData;
import com.inase.android.gocci.domain.model.PostData;
import com.inase.android.gocci.domain.model.TwoCellData;
import com.inase.android.gocci.utils.SavedData;
import com.inase.android.gocci.utils.map.HeatmapLog;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.util.ArrayList;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;\n\n""" + wrapInInterface(
        "API3Test", res2)


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
    return "interface {NAME} {{\n{CODE}}}".format(NAME=classname, CODE=ident(code))


def wrapInClass(classname, code):
    return "class {NAME} {{\n{CODE}}}".format(NAME=classname, CODE=ident(code))

def implClassWithImpl(code):
    return """class Impl implements API3Test {
        private static Impl sAPI3;

        public Impl() {
        }

        public static Impl getRepository() {
            if (sAPI3 == null) {
                sAPI3 = new Impl();
            }
            return sAPI3;
        }\n""" + code + "}"


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


def generateParameterRegexInInterface(path, parameters):
    localCode = path.title().replace('/', "") + "LocalCode"
    tmp = ["String " + s.key for s in parameters]
    return "Util." + localCode + " " + path.title().replace('/', '') + "ParameterRegex(" + ", ".join(tmp) + ");"


def generateResponseRegexInInterface(path, parameters):
    localCode = path.title().replace('/', "") + "LocalCode"
    tmp = ["String " + s.key for s in parameters]
    return "Util." + localCode + " " + path.title().replace('/', '') + "ResponseRegex(" + ", ".join(tmp) + ");"


def generateResponseInInterface(path):
    methodName = path.title().replace('/', "") + "Response"
    return "void " + methodName + "(JSONObject jsonObject, " + methodName + "Callback cb);"


def generateResponseCallbackInInterface(path):
    methodName = path.title().replace('/', "") + "ResponseCallback"
    res = "\tvoid onSuccess(); \n\n\tvoid onGlobalError(Util.GlobalCode globalCode); \n\n\tvoid onLocalError(String errorMessage);"
    return wrapInInterface(methodName, res)

def generateGetAPI(path, parameters):
    methodName = path.title().replace('/', "_")
    tmp = ["String " + s.key for s in parameters]
    res  = "public static String get" + cAmElCaSe(methodName) + "API(" + ", ".join(tmp) + ") {\n"
    res += "\treturn testurl + " + stringify(path + "/")
    if len(tmp) > 0:
        line = " + ".join([ "\"&"+ p.key + "=\" + " + p.key for p in parameters ])
        res += " + \"?" + line[2:]
    return res + ";\n}"

def generateParameterRegexInImpl(path, parameters):
    localCode = path.title().replace('/', "") + "LocalCode"
    tmp = ["String " + s.key for s in parameters]
    return "@Override\npublic Util." + localCode + " " + path.title().replace('/', '') + "ParameterRegex(" + ", ".join(tmp) + ") {\nreturn null;\n}"


def generateResponseRegexInImpl(path, parameters):
    localCode = path.title().replace('/', "") + "LocalCode"
    tmp = ["String " + s.key for s in parameters]
    return "@Override\npublic Util." + localCode + " " + path.title().replace('/', '') + "ResponseRegex(" + ", ".join(tmp) + ") {\nreturn null;\n}"


def generateResponseInImpl(path):
    methodName = path.title().replace('/', "") + "Response"
    return "@Override\npublic void " + methodName + "(JSONObject jsonObject, " + methodName + "Callback cb) {\n}"



