

import types
import textwrap
from util import *




def generate(everything):
    
    

    # everything.uriTokens.reverse()
    # for uri in everything.uriTokens:
        # print(generateValidatingJSONParser(uri.responses) + "\n\n\n")
    # return ""


    # print(generateValidatingJSONParser(everything.uriTokens[0].responses))




    # return ""



    masterClassName = "API3"

    for uri in everything.uriTokens:
        for para in uri.parameters:
            para.regex = regexify(para.regex)

    swift_intro  = staticLetString("baseurl", stringify(everything.apidict.pairs["baseurl"]))
    swift_intro += staticLetString("testurl", stringify(everything.apidict.pairs["testurl"]))

    swift_allErrorsAsEnum = generateEnum("GlobalCode", [ e.code for e in everything.globalErrors ] )

    tmp = { e.code: stringify(e.msg) for e in everything.globalErrors }
    swift_allErrorMessages = generateErrorMsgTable("globalErrorMessageTable", tmp)

    tmp = { e.code: e.code for e in everything.globalErrors }
    swift_codeReverseLookUpTable = generateCodeReverseLookUpTable("globalErrorReverseLookupTable", tmp)

    swift_APIClassOtherStuff = """
static var globalErrorMapping: [GlobalCode: (GlobalCode, String)->()] = [:]
static var onUnhandledError: (GlobalCode, String)->() = { print("FATAL: UNHANDLED API ERROR: \($0): \($1)") }

class func on(gcode: GlobalCode, perform:(GlobalCode, String)->()) {
    globalErrorMapping[gcode] = perform
}"""

    swift_handyGlobalErrorOns = generateHandyErrorOnGlobal([ e.code for e in everything.globalErrors ])

    uriTree = everything.transformURITokensFromFlatArrayToTreeStructureBasedOnTheirPath()


    def onURIToken(uri, nodeName):
        res  = "let apipath = " + stringify(uri.path) + "\n\n"
        res += "".join([ "var "+ x.key +": String?\n" for x in uri.parameters ]) + "\n"
        res += "var localErrorMapping: [LocalCode: (LocalCode, String)->()] = [:]\n\n"
        res += "var onUnhandledError: (LocalCode, String)->() = { print(\"FATAL: UNHANDLED API ERROR: \($0): \($1)\") }\n\n"
        res += generateEnum("LocalCode", [ e.code for e in uri.errors ] ) + "\n\n"

        res += generatePayloadType(uri.responses) + "\n"

        tmp = { e.code: stringify(e.msg) for e in uri.errors }
        res += generateSubErrorMsgTable("localErrorMessageTable", tmp) + "\n\n"
        tmp = [ e.code for e in uri.errors ]
        res += generateSubCodeReverseLookUpTable("localErrorReverseLookupTable", tmp) + "\n\n"

        res += otherStuffThatIsNeededButStatic(uri.absolutePath()) +"\n\n"

        if uri.responses.leafs:
            res += performFunctionWithPayload()
        else:
            res += performFunctionWithOUTPayload()

        res += "func on(code: LocalCode, perform: (LocalCode, String)->()){\n    self.localErrorMapping[code] = perform\n}\n\n"
        res += generateHandyErrorOnLocal([ e.code for e in uri.onlyExclusiveErrors ]) + "\n\n"
        res += generateParameterValidationForOneURI(uri) + "\n\n"
        res += generateValidatingJSONParser(uri.responses) + "\n\n"

        return res

    def subClassBuilder(eda): 
        classet = ""
        for node, v in eda.items():
            if type(v) is dict:
                code = ident(subClassBuilder(v))
                classet += "class {CN} {{\n\n{CODE} }}\n\n".format(CN=node, CODE=code)
            elif type(v) is types.URIToken:
                classet += wrapInClass(node, onURIToken(v, node), "APIRequestProtocol") + "\n"
                # classet += wrapInClass(node, onURIToken(v, node)) + "\n"
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

def generateSubErrorMsgTable(varname, errorMsgDict):
    res  = "static let localErrorMessageTable: [LocalCode: String] = {\n"
    res += "    var res: [LocalCode: String] = [:]\n"
    for code,msg in errorMsgDict.items():
        res += "    res[."+ code +"] = \n        " + msg + "\n"
    return res + "    return res\n}()\n"

def generateCodeReverseLookUpTable(varname, codes):
    res = "static let "+ varname +": [String: GlobalCode] = ["
    for c in codes:
        res += "\n    "+ stringify(c) +": ."+ c +","
    return res + "\n]"

def generateSubCodeReverseLookUpTable(varname, codes):
    res  = "static let localErrorReverseLookupTable: [String: LocalCode] = {\n"
    res += "    var res: [String: LocalCode] = [:]\n"
    for code in codes:
        res += "    res["+ stringify(code) +"] = ." + code + "\n"
    return res + "    return res\n}()\n"


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
    if let {PARA} = self.{PARA} where !APISupport.matches({PARA}, re: {REGEX}) {{
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
    if !APISupport.matches(value, re: {REGEX}) {{
        return API.Code.ERROR_PARAMETER_{PARAMETERUPCASE}_MALFORMED
    }}
}}
else {{
    return API.Code.ERROR_PARAMETER_{PARAMETERUPCASE}_MISSING
}}
""".format(MAPNAME=tablename, PARAMETER=parameter, REGEX=regex, PARAMETERUPCASE=parameter.upper())


def otherStuffThatIsNeededButStatic(absolutPath):
    return """
func preHandleLocalError(code: String, _ mmsg: String? = nil) -> Bool {{
    guard code == "SUCCESS" else {{
        guard let rcode = {AP}.localErrorReverseLookupTable[code] else {{
            APISupport.handleCommunicationFailure(.ERROR_UNKNOWN_ERROR, emsg: mmsg)
            return false
        }}
        handleLocalError(rcode, mmsg)
        return false
    }}
    return true
}}

func handleLocalError(code: LocalCode, _ mmsg: String? = nil) {{
    let msg = mmsg ?? {AP}.localErrorMessageTable[code] ?? "No error message defined"
    let handler = self.localErrorMapping[code] ?? self.onUnhandledError
    handler(code, msg)
}}

func validateSimpleResponse(json: [String: AnyObject], _ value: String, _ regex: String, _ misErr: LocalCode, _ malErr: LocalCode ) -> String? {{
    if let value = (json as? [String: String])?[value] {{
        if !APISupport.matches(value, re: regex) {{
            handleLocalError(malErr)
            return nil
        }}
        else {{
            return value
        }}
    }}
    else {{
        handleLocalError(misErr)
        return nil
    }}
}}

func validateSimpleArrayResponse(json: [String: AnyObject], _ value: String, _ regex: String, _ misErr: LocalCode, _ malErr: LocalCode ) -> [String]? {{
    if let values = (json as? [String: [String!]])?[value] {{
        var res: [String] = []
        for value in values {{
            if !APISupport.matches(value, re: regex) {{
                handleLocalError(malErr)
                return nil
            }}
            else {{
                res.append(value)
            }}
        }}
        return res
    }}
    else {{
        handleLocalError(misErr)
        return nil
    }}
}}
""".format(AP=absolutPath)

def performFunctionWithPayload():
    return """
func perform(and: (payload: Payload)->()) {
    APISupport.performNetworkRequest(self) { (code, msg, rawJSON) in
        if self.preHandleLocalError(code, msg) {
            if let payload = self.validateResponse(rawJSON) {
                and(payload: payload)
            }
        }
    }
}
"""

def performFunctionWithOUTPayload():
    return """
func perform(and: ()->()) {
    APISupport.performNetworkRequest(self) { (code, msg, _) in
        if self.preHandleLocalError(code, msg) {
            and()
        }
    }
}
"""

        

def generatePayloadType(responses):

    def onleaf(leaf, typ="String!"):
        nonlocal payload
        payload += "var {VARNAME}: {TYPE}\n".format(VARNAME=leaf.key, TYPE=typ)

    def onarray(array, typ="[String!] = []"):
        nonlocal payload
        payload += "var {VARNAME}: {TYPE}\n".format(VARNAME=array.key, TYPE=typ)

    def oncompoundarray(compoundarray):
        # oncomplextype(compoundarray, "[[String: {CLASSNAME}!]] = []", onarray)
        oncomplextype(compoundarray, "[{CLASSNAME}] = []", onarray)

    def ondict(dictleaf):
        # oncomplextype(dictleaf, "[String: {CLASSNAME}!] = [:]", onleaf)
        oncomplextype(dictleaf, "{CLASSNAME} = {CLASSNAME}()", onleaf)

    def oncomplextype(complextype, typestr, typegenerator):
        # This is magic^^
        nonlocal payload
        payload += "\n"
        clas = cAmElCaSe(complextype.key)
        typegenerator(complextype, typestr.format(CLASSNAME=clas))
        tmp = payload
        payload = ""
        visitor(clas, complextype)
        payload = tmp + payload
    
    def visitor(className, root):
        nonlocal payload
        root.traverse(onleaf, onarray, oncompoundarray, ondict)
        payload = "" if payload == "" else "class "+className+" {\n" + ident(payload) + "}\n"

    payload = ""
    visitor("Payload", responses)
    return payload


def generateValidatingJSONParser(responses):

    def onleaf(leaf):
        nonlocal validator
        validator += """{VARPATH}.{KEY} = validateSimpleResponse(json, "{KEY}", {RE},\n     .{MISERR}, .{MALERR})
if {VARPATH}.{KEY} != nil {{ return nil }}\n
""".format(VARPATH=".".join(varstack), KEY=leaf.key, RE=regexify(leaf.regex), MISERR=leaf.corrospondigMissingError.code, MALERR=leaf.corrospondigMalformError.code)

    def onarray(array):
        nonlocal validator
        validator += """{VARPATH}.{KEY} = validateSimpleArrayResponse(json, "{KEY}", {RE},\n    .{MISERR}, .{MALERR})
if {VARPATH}.{KEY} != nil {{ return nil }}\n
""".format(VARPATH=".".join(varstack), KEY=array.key, RE=regexify(array.regex), MISERR=array.corrospondigMissingError.code, MALERR=array.corrospondigMalformError.code)

    def oncompoundarray(compoundarray):
        nonlocal validator
        typestack.append(cAmElCaSe(compoundarray.key))
        varstack.append(compoundarray.key)
        pre = "if let arraydict = (json as? [String: [[String: {TYPEPATH}!]]])?[{KEY}] {{\n"
        pre += ident("for dict in arraydict {{\n    let tmp = {TYPEPATH}()\n\n")
        validator += pre.format(TYPEPATH=".".join(typestack), KEY=stringify(compoundarray.key)) 
        stepDownMagic(compoundarray, True)
        post = ident("    {VARPATH}.{KEY}.append(tmp)\n").format(VARPATH=".".join(varstack), KEY=compoundarray.key)+ "    }\n"
        validator += post +  "}\nelse {\n    handleLocalError(."+ compoundarray.corrospondigMissingError.code +")\n}\n\n"

    def ondict(dictleaf):
        nonlocal validator
        typestack.append(cAmElCaSe(dictleaf.key))
        varstack.append(dictleaf.key)
        pre = "if let dict = (json as? [String: [String: {TYPEPATH}!]])?[{KEY}] {{\n\n"
        validator += pre.format(TYPEPATH=".".join(typestack), KEY=stringify(dictleaf.key)) 
        stepDownMagic(dictleaf)
        validator += "}\nelse {\n    handleLocalError(."+ dictleaf.corrospondigMissingError.code +")\n}\n\n"

    def stepDownMagic(complextype, twice=False):
        nonlocal validator
        tmp = validator
        validator = ""
        complextype.traverse(onleaf, onarray, oncompoundarray, ondict)
        validator = tmp + (ident(ident(validator)) if twice else ident(validator))
        typestack.pop()
        varstack.pop()

    def masterWrap(entry):
        nonlocal validator
        pre = "func validateResponse(json: [String: AnyObject]) -> Payload? {\n    let payload = Payload()\n\n"
        entry.traverse(onleaf, onarray, oncompoundarray, ondict)
        validator = pre + ident(validator) + "\n    return payload\n}\n"
    
    typestack = ["Payload"]
    varstack  = ["payload"]
    validator = "" 
    masterWrap(responses)
    return "" if not responses.leafs else validator

l = """
    
    // JSON ARRAY OF DICT CASE
    if let arraydict = (json as? [String: [[String: Payload.GeoPosition!]]])?["geo_position"] {
        for dict in arraydict {
            let dict_of_geopositions = Payload.GeoPosition()
            
            dict_of_geopositions.long = self.validateSimpleResponse(dict, "username", "regex", .ERR, .ERR)
            if dict_of_geopositions.long != nil { return nil }
            
            dict_of_geopositions.long = self.validateSimpleResponse(dict, "username", "regex", .ERR, .ERR)
            if dict_of_geopositions.long != nil { return nil }
            
            res.geo_positions.append(dict_of_geopositions)
        }
    }
    else {
        handleLocalError(.ERROR_RESPONSE_IDENTITY_ID_MISSING)
    }
"""
