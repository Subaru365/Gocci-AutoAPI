
import datetime
from util import *
from tokens import *


def generate(everything):

    masterClassName = "API" + everything.version[0]

    header = """//
//   {MCN}.swift 
//   created by Markus Wanke 
//   created on {DATE}
//
//   WARNING======================================WARNING
//   WARNING                                      WARNING
//   WARNING      THIS FILE WAS AUTOGENERATED     WARNING
//   WARNING       NEVER EVER EDIT THIS FILE      WARNING
//   WARNING       ALWAYS GENERATE A NEW ONE      WARNING
//   WARNING                                      WARNING
//   WARNING======================================WARNING
//\n\n\nimport Foundation\n\n\n
""".format(MCN=masterClassName, DATE=datetime.datetime.now())

    
    swift_intro = staticLetString("version", stringify(everything.version))

    swift_intro += staticLetString("liveurl", stringify(everything.apidict.pairs["liveurl"]))
    swift_intro += staticLetString("testurl", stringify(everything.apidict.pairs["testurl"]))

    swift_allErrorsAsEnum = generateEnum("GlobalCode", [ e.code for e in everything.globalErrors ] )

    tmp = { e.code: stringify(e.msg) for e in everything.globalErrors }
    swift_allErrorMessages = generateErrorMsgTable("globalErrorMessageTable", tmp)

    tmp = { e.code: e.code for e in everything.globalErrors }
    swift_codeReverseLookUpTable = generateCodeReverseLookUpTable("globalErrorReverseLookupTable", tmp)


    uriTree = everything.transformURITokensFromFlatArrayToTreeStructureBasedOnTheirPath()

    def onURIToken(uri, nodeName):
        res  = "var apipath = " + stringify(uri.path) + "\n\n"
        res += generateParameterClass(uri.parameters) + "\n\n"
        res += "var localErrorMapping: [LocalCode: (LocalCode, String)->()] = [:]\n\n"
        res += generateEnum("LocalCode", [ e.code for e in uri.errors ] ) + "\n\n"

        res += "func canHandleErrorCode(code: String) -> Bool {\n    return " + nodeName + ".localErrorReverseLookupTable[code] != nil\n}\n\n"

        res += generatePayloadType(uri.responses) + "\n"

        tmp = { e.code: stringify(e.msg) for e in uri.errors }
        res += generateSubErrorMsgTable("localErrorMessageTable", tmp) + "\n\n"
        tmp = [ e.code for e in uri.errors ]
        res += generateSubCodeReverseLookUpTable("localErrorReverseLookupTable", tmp) + "\n\n"

        res += otherStuffThatIsNeededButStatic(nodeName) +"\n\n"

        if uri.responses.leafs:
            res += performFunctionWithPayload(nodeName)
        else:
            res += performFunctionWithOUTPayload(nodeName)

        res += "func on(code: LocalCode, perform: (LocalCode, String)->()){\n    self.localErrorMapping[code] = perform\n}\n\n"
        res += generateHandyErrorOnLocal([ e.code for e in uri.onlyExclusiveErrors ]) + "\n\n"
        res += generateParameterValidationForOneURI(uri) + "\n\n"
        res += generateNonValidatingJSONParser(uri.responses) + "\n\n"

        return res

    def subClassBuilder(eda): 
        classet = ""
        for node, v in eda.items():
            if type(v) is dict:
                code = ident(subClassBuilder(v))
                classet += "class {CN} {{\n\n{CODE} }}\n\n".format(CN=node, CODE=code)
            elif type(v) is URIToken:
                classet += wrapInClass(node, onURIToken(v, node), "APIRequest", "APIRequestProtocol") + "\n"
        return classet

    swift_subClasses = subClassBuilder(uriTree)

    # def sortarray(ar):
    # allcodes = list(ar.keys())
    # allcodes.sort(reverse=True)

    res  = swift_intro + "\n\n"
    res += swift_allErrorsAsEnum + "\n\n"
    res += swift_codeReverseLookUpTable + "\n\n"
    res += swift_allErrorMessages + "\n\n"
    res += swift_subClasses

    return header + wrapInClass(masterClassName, res)



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

def generateParameterClass(parameters):
    res = "".join([ "var "+ x.key +": String?\n" for x in parameters ]) + "\n"
    return wrapInClass("InternalParameterClass", res) + "\nlet parameters = InternalParameterClass()\n"


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
if let {PARA} = parameters.{PARA} {{
    if {PARA}.matches({REGEX}) {{
        res["{PARA}"] = {PARA}
    }}
    else {{
        handleLocalError(.{ECODE})
        return nil
    }}
}}"""
    optional_template = """
else {{
    handleLocalError(.{ECODE})
    return nil
}}
"""
    res = ""
    for p in uri.parameters:
        errormsg = stringify(p.corrospondigMalformError.msg)
        res += template.format(PARA=p.key, REGEX=regexify(p.regex), ECODE=p.corrospondigMalformError.code, EMMAL=errormsg)
        if not p.optional:
            errormsg = stringify(p.corrospondigMissingError.msg)
            res += optional_template.format(ECODE=p.corrospondigMissingError.code, EMMIS=errormsg)
    return pre + ident(res) + post


def generateOneParameterRegExCheck(tablename, parameter, regex):
    return  """
if let value = {MAPNAME}["{PARAMETER}"] {{
    if !value.matches({REGEX}) {{
        return API.Code.ERROR_PARAMETER_{PARAMETERUPCASE}_MALFORMED
    }}
}}
else {{
    return API.Code.ERROR_PARAMETER_{PARAMETERUPCASE}_MISSING
}}
""".format(MAPNAME=tablename, PARAMETER=parameter, REGEX=regexify(regex), PARAMETERUPCASE=parameter.upper())


def otherStuffThatIsNeededButStatic(classname):
    return """
func handleLocalError(code: LocalCode, _ mmsg: String? = nil) {{
    let msg = mmsg ?? {CN}.localErrorMessageTable[code] ?? "No error message defined"
    APILowLevel.sep("LOCAL ERROR OCCURED")
    APILowLevel.log("\(code): \(msg)")
    Util.runOnMainThread {{ self.localErrorMapping[code]?(code, msg) }}
    Util.runOnMainThread {{ self.privateOnAllErrorsCallback?() }}
}}
""".format(CN=classname)



def performFunctionWithPayload(classname):
    return """
private var callBackLink: ((payload: Payload)->())? = nil
                        
func retry() {{
    if let cb = callBackLink {{
        perform(cb)
    }}
}}

func perform(and: (payload: Payload)->()) {{
    callBackLink = and
    APILowLevel.performNetworkRequest(self) {{ (code, msg, json) in
        if code == "SUCCESS" {{
            if let payload = self.validateResponse_Payload(json) {{
                Util.runOnMainThread {{ and(payload: payload) }}
            }}
        }}
        else {{
            // guranteed by previous call to canHandleErrorCode
            self.handleLocalError({CN}.localErrorReverseLookupTable[code]!)
        }}
    }}
}}
""".format(CN=classname)

def performFunctionWithOUTPayload(classname):
    return """
private var callBackLink: (()->())? = nil
                        
func retry() {{
    if let cb = callBackLink {{
        perform(cb)
    }}
}}

func perform(and: ()->()) {{
    callBackLink = and
    APILowLevel.performNetworkRequest(self) {{ (code, msg, _) in
        if code == "SUCCESS" {{
            Util.runOnMainThread {{ and() }}
        }}
        else {{
            // guranteed by previous call to canHandleErrorCode
            self.handleLocalError({CN}.localErrorReverseLookupTable[code]!)
        }}
    }}
}}
""".format(CN=classname)

def typeToSwiftType(typ):
    if typ == ResponseType.INTEGER:
        return "Int!"
    elif typ == ResponseType.FLOAT:
        return "Double!"
    elif typ == ResponseType.BOOLEAN:
        return "Bool!"
    elif typ == ResponseType.STRING:
        return "String!"
    die("Swift parser can't handle type: " + leaf.typ)

def vardec(name, typ, defaultInit = False):
    if defaultInit:
        return "var {VARNAME}: {TYPE} = {TYPE}()\n".format(VARNAME=name, TYPE=typ)
    else:
        return "var {VARNAME}: {TYPE}\n".format(VARNAME=name, TYPE=typ)

def arrdec(name, typ):
    return "var {VARNAME}: [{TYPE}] = []\n".format(VARNAME=name, TYPE=typ)


def generatePayloadType(responses):

    def onleaf(leaf):
        nonlocal payload
        payload += vardec(leaf.key, typeToSwiftType(leaf.typ))

    def onarray(leaf):
        nonlocal payload
        payload += arrdec(leaf.key, typeToSwiftType(leaf.typ))

    def oncomplextype(complextype):
        # This is magic^^
        nonlocal payload
        classname = cAmElCaSe(complextype.key)
        if type(complextype) is ResponseDictonaryToken:
            payload += "\n" + vardec(complextype.key, classname, True)
        else:
            payload += "\n" + arrdec(complextype.key, classname)
        tmp = payload
        payload = ""
        visitor(classname, complextype)
        payload = tmp + payload
    
    def visitor(className, root):
        nonlocal payload
        root.traverse(onleaf, onarray, oncomplextype, oncomplextype)
        payload = "" if payload == "" else "class "+className+" {\n" + ident(payload) + "}\n"

    payload = ""
    visitor("Payload", responses)
    return payload





def swiftlyJSONtypeConversation(typ):
    if typ == ResponseType.INTEGER:
        return "int"
    elif typ == ResponseType.FLOAT:
        return "double"
    elif typ == ResponseType.BOOLEAN:
        return "bool"
    elif typ == ResponseType.STRING:
        return "string"
    else:
        die("Swift parser can't handle type: " + typ)



def verifySimpleResponse(key, typ, missingError):
    jsontyp = swiftlyJSONtypeConversation(typ)
    return """
if let {KEY} = json["{KEY}"]?.{TYP} {{
    res.{KEY} = {KEY}
}}
else {{
    handleLocalError(.{MISSERR})
    return nil
}}
""".format(KEY=key, TYP=jsontyp, MISSERR=missingError) 



def verifySimpleArrayResponse(key, typ, missingError):
    jsontyp = swiftlyJSONtypeConversation(typ)
    return """
if let {KEY}_array = json["{KEY}"]?.array {{
    for elem in {KEY}_array {{
        if let {KEY} = elem.{TYP} {{
            res.{KEY}.append({KEY})
        }}
        else {{
            handleLocalError(.{MISSERR})
            return nil
        }}
    }}
}}
else {{
    handleLocalError(.{MISSERR})
    return nil
}}
""".format(KEY=key, TYP=jsontyp, MISSERR=missingError) 



def verifyComplexResponsePreface(leaf, funcname):
    jsontype = "dictionary" if type(leaf) is ResponseDictonaryToken else "array"
    return """
if let {KEY}_unvalidated = json["{KEY}"]?.{JSONTYPE} {{
    guard let {KEY} = {FUNCNAME}({KEY}_unvalidated) else {{
        return nil // error handled in {FUNCNAME}
    }}
    res.{KEY} = {KEY}
}}
else {{
    handleLocalError(.{MISSERR})
    return nil
}}""".format(KEY=leaf.key , FUNCNAME=funcname , MISSERR=leaf.corrospondigMissingError.code, JSONTYPE=jsontype)



def verifyComplexArrayIntermediateStep(funcname, typepath, misserr):
    return """
func {FUNCNAME}(jsonArray: [JSON]) -> [{TP}]? {{
    var res: [{TP}] = []
    
    for jsonBlock in jsonArray {{
        guard let json = jsonBlock.dictionary else {{
            handleLocalError(.{MISSERR})
            return nil
        }}
        guard let one = {FUNCNAME}_Element(json) else {{
            return nil // error handled in {FUNCNAME}_Element
        }}
        res.append(one)
    }}
    
    return res
}}""".format(FUNCNAME=funcname, TP=typepath, MISSERR=misserr )



def makeValidatorFunction(funcname, typepath, content):
    vali = "func "+ funcname +"(json: [String: JSON]) -> " + typepath # Payload.RestsDict? {
    vali += "? {\n    let res = " + typepath + "()\n"
    for check in content:
        vali += ident(check) + "\n"
    return vali + "    return res\n}\n"



def generateNonValidatingJSONParser(responses):

    def onleaf(leaf):
        current.append(verifySimpleResponse(leaf.key, leaf.typ, leaf.corrospondigMissingError.code))

    def onarray(leaf):
        current.append(verifySimpleArrayResponse(leaf.key, leaf.typ, leaf.corrospondigMissingError.code))

    def oncomplex(leaf):
        if not leaf.leafs:
            return

        nonlocal current
        keystack.append(cAmElCaSe(leaf.key))
        funcname = "validateResponse_" + "_".join(keystack)
        current.append(verifyComplexResponsePreface(leaf, funcname))

        # save current depth level
        tmp = current
        current = []

        # step down
        leaf.traverse(onleaf, onarray, oncomplex, oncomplex)
        
        if type(leaf) is ResponseDictonaryToken:
            validators.append(makeValidatorFunction(funcname, ".".join(keystack), current))
        else:
            validators.append(verifyComplexArrayIntermediateStep(funcname, ".".join(keystack), leaf.corrospondigMissingError.code))
            validators.append(makeValidatorFunction(funcname + "_Element", ".".join(keystack), current))

        # stack cleanup
        keystack.pop()
        current = tmp


    current = []
    validators = []
    keystack = []
    
    oncomplex(responses)

    return "\n".join(reversed(validators))




