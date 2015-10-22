


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
        self.onlyExclusiveErrors = []

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

    def absolutePath(self):
        return self.pathComponents()[-1]

    def addError(self, x):
        self.errors.append(x)
    def addParameter(self, x):
        self.parameters.append(x)
    def addResponse(self, x):
        self.responses = x



    def autoGenerateErrorsForOneParameter(self, p):
        if not p.optional:
            msg = "Parameter '"+ p.key +"' does not exist." 
            p.corrospondigMissingError = ErrorToken("ERROR_PARAMETER_" + p.key.upper() + "_MISSING", msg)
            self.errors.append(p.corrospondigMissingError)

        msg = "Parameter '"+ p.key +"' is malformed. Should correspond to '"+ p.regex +"'"
        p.corrospondigMalformError = ErrorToken("ERROR_PARAMETER_" + p.key.upper() + "_MALFORMED", msg)
        self.errors.append(p.corrospondigMalformError)


    def autoGenerateMissingErrorForOneResponse(self, r, epath):
        msg = "Response '"+ r.key +"' was not received"
        r.corrospondigMissingError = ErrorToken("ERROR_RESPONSE_" + epath + "_" + r.key.upper() + "_MISSING", msg)
        self.errors.append(r.corrospondigMissingError)

    def autoGenerateMalformErrorForOneResponse(self, r, epath):
        msg = "Response '"+ r.key +"' is malformed. Should correspond to '"+ r.regex +"'"
        r.corrospondigMalformError = ErrorToken("ERROR_RESPONSE_" + epath + "_" + r.key.upper() + "_MALFORMED", msg)
        self.errors.append(r.corrospondigMalformError)

    def autoGenerateMalformErrorsForAllResponses(self, resps):
        def onsimple(l):
            self.autoGenerateMissingErrorForOneResponse(l, "_".join(keystack))
            self.autoGenerateMalformErrorForOneResponse(l, "_".join(keystack))
        def oncomplex(l):
            self.autoGenerateMissingErrorForOneResponse(l, "_".join(keystack))
            keystack.append(l.key.upper())
            l.traverse(onsimple, onsimple, oncomplex, oncomplex)
            keystack.pop()


        keystack = []
        resps.traverse(onsimple, onsimple, oncomplex, oncomplex)

    def autoGenerateMalformErrors(self):
        self.onlyExclusiveErrors = list(self.errors)
        for p in self.parameters:
            self.autoGenerateErrorsForOneParameter(p)
        self.autoGenerateMalformErrorsForAllResponses(self.responses)

class ParameterToken:
    def __init__(self, key, re, optional=False):
        self.key = key
        self.regex = re
        self.optional = optional
        self.corrospondigMalformError = None
        self.corrospondigMissingError = None

    def __str__(self):
        return "PARAMETER: " + self.key + " " + self.regex

class AbstractResponse(object):
    def __init__(self, key):
        self.key = key
        self.corrospondigMalformError = None
        self.corrospondigMissingError = None

class ResponseToken(AbstractResponse):
    def __init__(self, key, re):
        super().__init__(key)
        self.regex = re

    def __str__(self):
        return "RESPONSE: " + self.key + " " + self.regex


class ResponseArrayToken(AbstractResponse):
    def __init__(self, key, re, itemcount=None):
        super().__init__(key)
        self.regex = re
        self.itemcount = itemcount

    def __str__(self):
        return "RESPONSE: ARRAY OF [" + self.key + "] " + self.regex

class ResponseDictonaryToken(AbstractResponse):
    def __init__(self, key, level):
        super().__init__(key)
        self.leafs = []
        self.identlevel = level

    def add(self, a):
        self.leafs.append(a)

    def recursive_traverse(self, onleaf, onarray):
        for resp in self.leafs:
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
        for resp in self.leafs:
            if type(resp) is ResponseToken:
                onleaf(resp)
            elif type(resp) is ResponseArrayToken:
                onarray(resp)
            elif type(resp) is ResponseArrayCompoundToken:
                oncompoundarray(resp)
            elif type(resp) is ResponseDictonaryToken:
                ondict(resp)

    def __iter__(self):
        return iter(self.leafs)

    def __str__(self):
        res = "DICTONARY NAMED " + self.key + ":"
        for r in self.leafs:
            res += "\n"+ ("    "*self.identlevel) + str(r)
        return res

class ResponseArrayCompoundToken(AbstractResponse):
    def __init__(self, key, level, itemcount = None):
        super().__init__(key)
        self.itemcount = itemcount
        self.leafs = []
        self.identlevel = level

    def add(self, a):
        self.leafs.append(a)

    def recursive_traverse(self, onleaf, onarray):
        for resp in self.leafs:
            if type(resp) is ResponseToken:
                onleaf(resp)
            elif type(resp) is ResponseArrayToken:
                onarray(resp)
            elif type(resp) is ResponseArrayCompoundToken:
                resp.recursive_traverse(onleaf, onarray)
            elif type(resp) is ResponseDictonaryToken:
                resp.recursive_traverse(onleaf, onarray)

    def traverse(self, onleaf=lambda x:x, onarray=lambda x:x, oncompoundarray=lambda x:x, ondict=lambda x:x):
        for resp in self.leafs:
            if type(resp) is ResponseToken:
                onleaf(resp)
            elif type(resp) is ResponseArrayToken:
                onarray(resp)
            elif type(resp) is ResponseArrayCompoundToken:
                oncompoundarray(resp)
            elif type(resp) is ResponseDictonaryToken:
                ondict(resp)

    def __iter__(self):
        return iter(self.leafs)

    def __str__(self):
        res = "ARRAY OF SUBSTRUCTURE " + self.key + ":"
        for r in self.leafs:
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
