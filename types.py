


#{
#   "version": "3.1",
#   "code": 100,
#   "uri":"/v3/mobile/auth/signup",
#   "identifier":"SUCCESS",
#   "message": "successful api request",
#   "payload:": 
#   {
#      "token":"eyJrfehfhwiehfwhfiw877ef7wf7w......"
#   }
#}
# API VERSION 		"version" 		"\d+\.\d+"
# API RESPONSE_CODE 	"code" 			"\d\d\d"
# API REQUESTED_URI 	"uri" 			"/[a-z/]+"
# API IDENTIFIER 		"identifier" 	"[A-Z_]+"
# API MESSAGE 		"message" 		"\w+"
# API PAYLOAD 		"payload" 		"valid_json"

class URIToken:

    def __init__(self, ver):
        self.version = ver
        self.response_code = None
        self.requested_uri = None
        self.identifier = None
        self.message = None
        self.payload = None


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

    def addError(self, x):
        self.errors.append(x)
    def addParameter(self, x):
        self.parameters.append(x)
    def addResponse(self, x):
        self.responses.append(x)


    def autoGenerateMalformErrors(self):
        for p in self.parameters:
            msg = "Parameter '"+ p.key +"' is malformed. Should correspond to '"+ p.regex +"'"
            self.errors.append(ErrorToken("ERROR_PARAMETER_" + p.key.upper() + "_MALFORMED", msg))
        for r in self.responses:
            msg = "Response '"+ r.key +"' is malformed. Should correspond to '"+ r.regex +"'"
            self.errors.append(ErrorToken("ERROR_RESPONSE_" + r.key.upper() + "_MALFORMED", msg))

    def setErrorCodesAscending(self):
        i = 300
        for e in self.errors: 
            e.setErrorCode(str(i))
            i += 1
            


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
    def __init__(self, identifier, msg, ecode="0"):
        self.identifier = identifier
        self.msg = msg
        self.code = ecode

    def setErrorCode(self, c):
        self.code = c

    def __str__(self):
        return "ERROR: " + self.identifier +" "+ self.code +" "+ self.msg



class Enum(set):
    def __getattr__(self, name):
        if name in self:
            return name
        raise AttributeError
