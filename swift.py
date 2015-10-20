

import types
import textwrap
from util import *

# class Stack:
    # def __init__(self):
        # self.items = []

    # def push(self, item):
        # self.items.append(item)

    # def pop(self):
        # return self.items.pop()

    # def last(self):
        # return self.items[-1]

    # def plusDict(self, k, v):
        # print(self.items)
        # # try:
        # self.items[-1][k] = v
        # # except:
            # # self.items.append({k:v})

    # def plusString(self, st):
        # # try:
            # self.items[-1] = self.items[-1] + st
        # # except:
            # # self.items.append(st)

    # def peek(self):
        # return self.items[len(self.items)-1]

    # def join(self, joiner=""):
        # return joiner.join(self.items)


def generate(everything):

    # def generateConstructor(pairs):
        # res  = "init(" + ", ".join([ k+": "+t for k,t in pairs.items() ]) + ") {\n"
        # res += "".join([ "    self.{k} = {k}\n".format(k=key) for key in pairs.keys() ])
        # return res + "}\n"

    
    def onleaf(leaf):
        nonlocal payload
        payload += "var " + leaf.key + ": String\n"

    def onarray(array):
        nonlocal payload
        payload += "var " + array.key + ": [String]\n"

    def oncompoundarray(compoundarray):
        nonlocal payload
        # compoundarray.traverse(onleaf, onarray, oncompoundarray, ondict)

    def ondict(dictleaf):
        nonlocal payload
        clas = cAmElCaSe(dictleaf.key)
        payload += "\nvar " + dictleaf.key + ": " + clas  + "\n"
        tmp = payload
        payload = ""
        visitor(clas, dictleaf)
        payload = tmp + "\n" + payload + "\n"
    
    def visitor(className, root):
        nonlocal payload
        root.traverse(onleaf, onarray, oncompoundarray, ondict)
        payload = "class "+className+" {\n" + ident(payload) + "}\n\n"

    payload = ""
    visitor("Payload", everything.uriTokens[0].responses)
    print(payload)

    # for uri in everything.uriTokens:
        # visitor("Payload", uri.responses)

    
    
    return ""
    masterClassName = "API3"

    def forEachLeaf(resp):
        resp.regex = regexify(resp.regex)

    for uri in everything.uriTokens:
        for para in uri.parameters:
            para.regex = regexify(para.regex)
        uri.responses.recursive_traverse(forEachLeaf, lambda x:x)

    swift_intro  = staticLetString("baseurl", stringify(everything.apidict.pairs["baseurl"]))
    swift_intro += staticLetString("testurl", stringify(everything.apidict.pairs["testurl"]))

    swift_allErrorsAsEnum = generateEnum("GlobalCode", [ e.code for e in everything.globalErrors ] )

    tmp = { e.code: stringify(e.msg) for e in everything.globalErrors }
    swift_allErrorMessages = generateErrorMsgTable("globalErrorMessageTable", tmp)

    tmp = { e.code: e.code for e in everything.globalErrors }
    swift_codeReverseLookUpTable = generateCodeReverseLookUpTable("globalErrorReverseLookupTable", tmp)

    swift_APIClassOtherStuff = """
static var globalErrorMapping: [GlobalCode: (GlobalCode, String)->()] = [:]
static var onUnhandledError: (GlobalCode, String)->() = """ + masterClassName + """.unhandledErrorDefault

private class func unhandledErrorDefault(c: GlobalCode, m: String) {
    print("FATAL: UNHANDLED API ERROR: \(c): \(m)")
}

class func on(gcode: GlobalCode, perform:(GlobalCode, String)->()) {
    globalErrorMapping[gcode] = perform
}"""

    swift_handyGlobalErrorOns = generateHandyErrorOnGlobal([ e.code for e in everything.globalErrors ])

    uriTree = everything.transformURITokensFromFlatArrayToTreeStructureBasedOnTheirPath()


    def beforeNode(node, nodeName):
        return "class " + nodeName + "{\n\n"

    def afterNode(node, nodeName):
        return "}\n\n" 

    def onURIToken(uri, nodeName):
        res  = "let apipath = " + stringify(uri.path) + "\n\n"
        res += "".join([ "var "+ x.key +": String?\n" for x in uri.parameters ]) + "\n"
        res += "var localErrorMapping: [LocalCode: (LocalCode, String)->()] = [:]\n\n"
        res += generateEnum("LocalCode", [ e.code for e in uri.errors ] ) + "\n\n"
        tmp = { e.code: stringify(e.msg) for e in uri.errors }
        res += generateSubErrorMsgTable("localErrorMessageTable", tmp, toAPIPath(masterClassName, uri.path)) + "\n\n"
        tmp = { e.code: e.code for e in uri.errors }
        res += generateSubCodeReverseLookUpTable("localErrorReverseLookupTable", tmp, toAPIPath(masterClassName, uri.path)) + "\n\n"
        res += "func on(code: LocalCode, perform: (LocalCode, String)->()){\n    self.localErrorMapping[code] = perform\n}\n\n"
        res += generateHandyErrorOnLocal([ e.code for e in uri.errors ]) + "\n\n"
        res += generateParameterValidationForOneURI(uri) + "\n\n"
        return res

    def subClassBuilder(eda): 
        classet = ""
        for node, v in eda.items():
            if type(v) is dict:
                clas  = beforeNode(v, node)
                clas += ident(subClassBuilder(v))
                clas += afterNode(v, node)
                classet += clas
            elif type(v) is types.URIToken:
                # classet += wrapInClass(node, onURIToken(v, node), "APIRequestProtocol") + "\n"
                classet += wrapInClass(node, onURIToken(v, node)) + "\n"
        return classet

    swift_subClasses = subClassBuilder(uriTree)

    # def sortarray(ar):
    # allcodes = list(ar.keys())
    # allcodes.sort(reverse=True)

    res = swift_intro + "\n\n"
    res += swift_allErrorsAsEnum + "\n\n"
    res += swift_codeReverseLookUpTable + "\n\n"
    res += swift_allErrorMessages + "\n\n"
    res += swift_handyGlobalErrorOns + "\n\n"
    res += swift_APIClassOtherStuff + "\n\n"
    res += swift_subClasses + "\n\n"

    return wrapInClass("API3", res)



def toAPIPath(masterclassname, path):
    return masterclassname + path.replace('/', '.')

def staticLetString(varname, value):
    return "static let {vn} = {v}\n".format(vn=varname, v=value)


def wrapInClass(classname, code, *extends):
    ex = "" if len(extends)==0 else ": " + ", ".join(extends)
    return "class {NAME}{EXTENDS} {{\n{CODE}}}\n".format(NAME=classname, EXTENDS=ex, CODE=ident(code))

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


def generateSubErrorMsgTable(varname, errorMsgDict, apipath):
    res  = "static let localErrorMessageTable: [LocalCode: String] = "+apipath+".xCodeBugProtectionLocalErrorMessageTableGenerator()\n\n"
    res += "private class func xCodeBugProtectionLocalErrorMessageTableGenerator() -> [LocalCode: String] {\n"
    res += "    var res: [LocalCode: String] = [:]\n"
    for code,msg in errorMsgDict.items():
        res += "    res[."+ code +"] = \n        " + msg + "\n"
    return res + "    return res\n}\n"

def generateCodeReverseLookUpTable(varname, codes):
    res = "static let "+ varname +": [String: GlobalCode] = ["
    for c in codes:
        res += "\n    "+ stringify(c) +": ."+ c +","
    return res + "\n]"

def generateSubCodeReverseLookUpTable(varname, codes, apipath):
    res  = "static let localErrorReverseLookupTable: [String: LocalCode] = "+apipath+".xCodeBugProtectionLocalReverseLookUpTableGenerator()\n\n"
    res += "private class func xCodeBugProtectionLocalReverseLookUpTableGenerator() -> [String: LocalCode] {\n"
    res += "    var res: [String: LocalCode] = [:]\n"
    for code in codes:
        res += "    res["+ stringify(code) +"] = ." + code + "\n"
    return res + "    return res\n}\n"



def generateHandyErrorOnGlobal(ecodes):
    template = """
class func on_{ec}(perform:(GlobalCode, String)->()) {{
    globalErrorMapping[.{ec}] = perform\n}}"""
    return "".join( [ template.format(ec=ec) for ec in ecodes ] )

def generateHandyErrorOnLocal(ecodes):
    template = """
func on_{ec}(perform:(LocalCode, String)->()) {{
    localErrorMapping[.{ec}] = perform\n}}"""
    return "".join( [ template.format(ec=ec) for ec in ecodes ] )


def generateParameterValidationForOneURI(uri):
    pre = """
func validateParameterPairs() -> [String: String]? {\n
    var res: [String: String] = [:]\n\n"""
    post = "\n    return res\n}\n"
    template = """
if let {PARA} = self.{PARA} {{
    if let {PARA} = self.{PARA} where !APIUtil.matches({PARA}, re: {REGEX}) {{
        let emsg = {EMMAL}
        self.localErrorMapping[.{ECODE}]?(.{ECODE}, emsg)
        return nil
    }}
    else {{
        res["{PARA}"] = {PARA}
    }}
}}"""
    optional_template = """
else {{
    let emsg = {EMMIS} 
    self.localErrorMapping[.{ECODE}]?(.{ECODE}, emsg)
    return nil
}}
"""
    res = ""
    for p in uri.parameters:
        errormsg = stringify(p.corrospondigMalformError.msg)
        res += template.format(PARA=p.key, REGEX=p.regex, ECODE=p.corrospondigMalformError.code, EMMAL=errormsg)
        if not p.optional:
            errormsg = stringify(p.corrospondigMissingError.msg)
            res += optional_template.format(ECODE=p.corrospondigMissingError.code, EMMIS=errormsg)
    return pre + ident(res) + post


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
