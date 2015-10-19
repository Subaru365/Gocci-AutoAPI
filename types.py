


class Everything:
    def __init__(self, v, bf, ge, uris):
        self.version = v       # Simple String
        self.apidict = bf      # Like a dict
        self.globalErrors = ge # Array of ErrorToken
        self.uriTokens = uris  # Array of URIToken


    def transformURITokensFromFlatArrayToTreeStructureBasedOnTheirPath(self):
        def stepDown(thisDict, rest, uri):
            if len(rest) > 1 and rest[0] in thisDict:
                stepDown(thisDict[rest[0]], rest[1:], uri)
            elif len(rest) > 1: 
                thisDict[rest[0]] = {}
                stepDown(thisDict[rest[0]], rest[1:], uri)
            else:
                thisDict[rest[0]] = uri

        uriTree = {} 
        for uri in self.uriTokens:
            stepDown(uriTree, uri.pathComponents(), uri)
        return uriTree

class APIDict:
    def __init__(self):
        self.pairs = dict()

    def addPair(self, key, value):
        self.pairs[key] = value

    def __str__(self):
        res =  "API DICT:"
        for k,v in self.pairs.items():
            res += "\n\t{}:\t{}".format(k,v)
        return res


class URIToken:

    def __init__(self, p):
        self.path = p
        self.parameters = []
        self.responses = ResponseDictonaryToken("dummy for URIs with no responses", 0)
        self.errors = []

    def __str__(self):
        res = "URI Path: " + self.path
        for x in self.parameters:
            res += ("\n    " + str(x))
        for x in self.responses:
            res += ("\n    " + str(x))
        for x in self.errors:
            res += ("\n    " + str(x))
        return res

    def normalizedKey(self):
        return self.path.replace('/', '__')

    def pathComponents(self):
        return self.path[1:].split("/")

    def addError(self, x):
        self.errors.append(x)
    def addParameter(self, x):
        self.parameters.append(x)
    def addResponse(self, x):
        self.responses = x



    def autoGenerateMalformErrorForOneParameter(self, p):
        msg = "Parameter '"+ p.key +"' does not exist." 
        self.errors.append(ErrorToken("ERROR_PARAMETER_" + p.key.upper() + "_MISSING", msg))
        msg = "Parameter '"+ p.key +"' is malformed. Should correspond to '"+ p.regex +"'"
        self.errors.append(ErrorToken("ERROR_PARAMETER_" + p.key.upper() + "_MALFORMED", msg))


    def autoGenerateMalformErrorForOneResponse(self, r):
        msg = "Response '"+ r.key +"' was not received"
        self.errors.append(ErrorToken("ERROR_RESPONSE_" + r.key.upper() + "_MISSING", msg))
        msg = "Response '"+ r.key +"' is malformed. Should correspond to '"+ r.regex +"'"
        self.errors.append(ErrorToken("ERROR_RESPONSE_" + r.key.upper() + "_MALFORMED", msg))

    def autoGenerateMalformErrorsForAllResponses(self, resps):
        def onleaf(l):
            self.autoGenerateMalformErrorForOneResponse(l)
        def onarray(l):
            self.autoGenerateMalformErrorForOneResponse(l)

        resps.recursive_traverse(onleaf, onarray)

    def autoGenerateMalformErrors(self):
        for p in self.parameters:
            self.autoGenerateMalformErrorForOneParameter(p)
        self.autoGenerateMalformErrorsForAllResponses(self.responses)

class ParameterToken:
    def __init__(self, key, re, tags=None):
        self.key = key
        self.regex = re
        # TODO tags

    def __str__(self):
        return "PARAMETER: " + self.key + " " + self.regex

# TODO tags
class ResponseToken:
    def __init__(self, key, re):
        self.key = key
        self.regex = re

    def __str__(self):
        return "RESPONSE: " + self.key + " " + self.regex


class ResponseArrayToken:
    def __init__(self, key, re, itemcount=None):
        self.key = key
        self.regex = re
        self.itemcount = itemcount

    def __str__(self):
        return "RESPONSE: ARRAY OF [" + self.key + "] " + self.regex

class ResponseDictonaryToken:
    def __init__(self, key, level):
        self.key = key
        self.leafes = []
        self.identlevel = level

    def add(self, a):
        self.leafes.append(a)

    def recursive_traverse(self, onleaf, onarray):
        for resp in self.leafes:
            if type(resp) is ResponseToken:
                onleaf(resp)
            elif type(resp) is ResponseArrayToken:
                onarray(resp)
            elif type(resp) is ResponseArrayCompoundToken:
                resp.recursive_traverse(onleaf, onarray)
            elif type(resp) is ResponseDictonaryToken:
                resp.recursive_traverse(onleaf, onarray)

    # def traverse(self, onleaf=lambda x:x, onarray=lambda x:x, onenterarray=lambda x:x, onleavearray=lambda x:x, onenterdict=lambda x:x, onleavedict=lambda x:x)
    def traverse(self, onleaf=lambda x:x, onarray=lambda x:x, oncompoundarray=lambda x:x, ondict=lambda x:x):
        for resp in self.leafes:
            if type(resp) is ResponseToken:
                onleaf(resp)
            elif type(resp) is ResponseArrayToken:
                onarray(resp)
            elif type(resp) is ResponseArrayCompoundToken:
                oncompoundarray(resp)
            elif type(resp) is ResponseDictonaryToken:
                ondict(resp)

    def __iter__(self):
        return iter(self.leafes)

    def __str__(self):
        res = "DICTONARY NAMED " + self.key + ":"
        for r in self.leafes:
            res += "\n"+ ("    "*self.identlevel) + str(r)
        return res

class ResponseArrayCompoundToken:
    def __init__(self, key, level, itemcount = None):
        self.key = key
        self.itemcount = itemcount
        self.leafes = []
        self.identlevel = level

    def add(self, a):
        self.leafes.append(a)

    def recursive_traverse(self, onleaf, onarray):
        for resp in self.leafes:
            if type(resp) is ResponseToken:
                onleaf(resp)
            elif type(resp) is ResponseArrayToken:
                onarray(resp)
            elif type(resp) is ResponseArrayCompoundToken:
                resp.recursive_traverse(onleaf, onarray)
            elif type(resp) is ResponseDictonaryToken:
                resp.recursive_traverse(onleaf, onarray)

    def traverse(self, onleaf=lambda x:x, onarray=lambda x:x, oncompoundarray=lambda x:x, ondict=lambda x:x):
        for resp in self.leafes:
            if type(resp) is ResponseToken:
                onleaf(resp)
            elif type(resp) is ResponseArrayToken:
                onarray(resp)
            elif type(resp) is ResponseArrayCompoundToken:
                oncompoundarray(resp)
            elif type(resp) is ResponseDictonaryToken:
                ondict(resp)

    def __iter__(self):
        return iter(self.leafes)

    def __str__(self):
        res = "ARRAY OF SUBSTRUCTURE " + self.key + ":"
        for r in self.leafes:
            res += "\n"+ ("    "*self.identlevel) + str(r)
        return res

class ErrorToken:
    def __init__(self, code, msg):
        self.msg = msg
        self.code = code

    def __str__(self):
        return "ERROR: " + self.code +" "+ self.msg



class Enum(set):
    def __getattr__(self, name):
        if name in self:
            return name
        raise AttributeError
