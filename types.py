


class Everything:
    def __init__(self, bf, ge, uris):
        self.baseframe = bf
        self.globalErrors = ge
        self.uriTokens = uris

class BaseFrame:

    def __init__(self):
        self.validation_pairs = dict()

    def addPair(self, key, value):
        self.validation_pairs[key] = value

    def getPairs(self):
        return validation_pairs

    def __str__(self):
        res =  "API BASEFRAME:"
        for k,v in self.validation_pairs.items():
            res += "\n\t{}:\t{}".format(k,v)
        return res


class URIToken:

    def __init__(self, p):
        self.path = p
        self.parameters = []
        self.responses = []
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

    def addError(self, x):
        self.errors.append(x)
    def addParameter(self, x):
        self.parameters.append(x)
    def addResponse(self, x):
        self.responses.append(x)


    def autoGenerateMalformErrors(self):
        for p in self.parameters:
            msg = "Parameter '"+ p.key +"' does not exist." 
            self.errors.append(ErrorToken("ERROR_PARAMETER_" + p.key.upper() + "_MISSING", msg))
        for p in self.parameters:
            msg = "Parameter '"+ p.key +"' is malformed. Should correspond to '"+ p.regex +"'"
            self.errors.append(ErrorToken("ERROR_PARAMETER_" + p.key.upper() + "_MALFORMED", msg))
        for r in self.responses:
            msg = "Response '"+ r.key +"' was not received"
            self.errors.append(ErrorToken("ERROR_RESPONSE_" + r.key.upper() + "_MISSING", msg))
        for r in self.responses:
            msg = "Response '"+ r.key +"' is malformed. Should correspond to '"+ r.regex +"'"
            self.errors.append(ErrorToken("ERROR_RESPONSE_" + r.key.upper() + "_MALFORMED", msg))

class ParameterToken:
    def __init__(self, key, re, tags=None):
        self.key = key
        self.regex = re
        # TODO tags

    def __str__(self):
        return "PARAMETER: " + self.key + " " + self.regex

class ResponseToken:
    def __init__(self, key, re, tags=None):
        self.key = key
        self.regex = re
        # TODO tags

    def __str__(self):
        return "RESPONSE: " + self.key + " " + self.regex

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
