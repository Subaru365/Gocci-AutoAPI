

import json
from util import *

def generate(everything):

    res = {}
    # res["api"] = {}
    # res["globalerror"] = {}
    res["uris"] = {}

    for uri in everything.uriTokens:
        res["uris"][uri.path] = { "parameters": {}, "responses": {}, "errors": {} }

    for uri in everything.uriTokens:
        res["uris"][uri.path]["parameters"] = { para.key : para.regex for para in uri.parameters }

    for uri in everything.uriTokens:
        res["uris"][uri.path]["errors"] = { err.code : err.msg for err in uri.errors }

    
    def onleaf(x):
        current[x.key] = x.regex
    def onarray(x):
        current[x.key] = [x.regex]
    def oncompoundarray(x):
        nonlocal current
        tmp = current
        a = {}
        current[x.key] = [a]
        current = a
        x.traverse(onleaf, onarray, oncompoundarray, ondict)
        current = tmp
    def ondict(x):
        nonlocal current
        tmp = current
        current[x.key] = {}
        current = current[x.key]
        x.traverse(onleaf, onarray, oncompoundarray, ondict)
        current = tmp
   

    for uri in everything.uriTokens:
        current = res["uris"][uri.path]["responses"]
        uri.responses.traverse(onleaf, onarray, oncompoundarray, ondict)


    return json.dumps(res, indent=4, sort_keys=True)

