from util import *

def generate(everything):
    for uri in everything.uriTokens:
        for para in uri.parameters:
            para.regex = regexify(para.regex)

    java_intro = staticFinalString("baseurl", stringify(everything.apidict.pairs["baseurl"]))
    java_intro += staticFinalString("testurl", stringify(everything.apidict.pairs["testurl"]))

    java_allErrorsAsEnum = generateEnum("GlobalCode", [e.code for e in everything.globalErrors])

    tmp = {e.code: stringify(e.msg) for e in everything.globalErrors}
    java_allErrorMessages = generateErrorMsgTable("globalErrorMessageTable", tmp, "GlobalCode")

    tmp = {e.code: e.code for e in everything.globalErrors}
    java_codeReverseLookUpTable = generateCodeReverseLookUpTable("globalErrorReverseLookupTable", tmp, "GlobalCode")

    uriTree = everything.transformURITokensFromFlatArrayToTreeStructureBasedOnTheirPath()

    def onURIToken(uri, nodeName):

        return res

    def subClassBuilder(eda):
        classet = ""

        return classet

    swift_subClasses = subClassBuilder(uriTree)

    # def sortarray(ar):
    # allcodes = list(ar.keys())
    # allcodes.sort(reverse=True)

    res = java_intro + "\n"
    res += java_allErrorsAsEnum + "\n\n"
    res += java_codeReverseLookUpTable + "\n\n"
    res += java_allErrorMessages + "\n"

    return wrapInClass("Util", res)


def staticFinalString(varname, value):
    return "private static final {vn} = {v};\n".format(vn=varname, v=value)


def wrapInInterface(classname, code):
    return "interface {NAME} {{\n{CODE}}}\n".format(NAME=classname, CODE=ident(code))


def wrapInClass(classname, code):
    return "public class {NAME} {{\n{CODE}}}\n".format(NAME=classname, CODE=ident(code))


def generateEnum(enumname, items):
    res = "public enum " + enumname + " {"
    for i in items:
        res += "\n  " + i + ","
    return res + "\n}"


def generateErrorMsgTable(varname, errorMsgDict, enumname):
    res = "public static String " + varname + "(" + enumname + " code) {\n\tString message = null;\n\tswitch(code) {"
    for k, v in errorMsgDict.items():
        res += "\n\t\tcase " + k + ":\n\t\t\tmessage = " + v + ";\n\t\t\tbreak;"
    return res + "\n\t}\n\treturn message;\n}"


def generateCodeReverseLookUpTable(varname, codes, enumname):
    res = "public static " + enumname + " " + varname + "(String code) {\n\t" + enumname + " enumCode = null;\n\tswitch(code) {"
    for c in codes:
        res += "\n\t\tcase " + stringify(c) + ":\n\t\t\tenumCode = " + enumname + "." + c + ";\n\t\t\tbreak;"
    return res + "\n\t}\n\treturn enumCode;\n}"
