

import json
from util import *

def generate(everything):

    res = {}

    res["api"] = everything.apidict.pairs
    res["globalerror"] = { err.code : err.msg for err in everything.globalErrors }

    res["uris"] = {}

    for uri in everything.uriTokens:
        res["uris"][uri.path] = { "parameters": {}, "responses": {}, "errors": {} }

    for uri in everything.uriTokens:
        res["uris"][uri.path]["parameters"] = { para.key : para.regex for para in uri.parameters }

    for uri in everything.uriTokens:
        res["uris"][uri.path]["errors"] = { err.code : err.msg for err in uri.errors }

    
    def onleaf(leaf):
        current[leaf.key] = leaf.regex

    def onarray(array):
        current[array.key] = [array.regex]

    def oncompoundarray(compoundarray):
        nonlocal current
        tmp = current
        ref = {}
        current[compoundarray.key] = [ref]
        current = ref
        compoundarray.traverse(onleaf, onarray, oncompoundarray, ondict)
        current = tmp

    def ondict(dictleaf):
        nonlocal current
        tmp = current
        current[dictleaf.key] = {}
        current = current[dictleaf.key]
        dictleaf.traverse(onleaf, onarray, oncompoundarray, ondict)
        current = tmp
   

    for uri in everything.uriTokens:
        current = res["uris"][uri.path]["responses"]
        uri.responses.traverse(onleaf, onarray, oncompoundarray, ondict)


    return json.dumps(res, indent=4, sort_keys=True)

