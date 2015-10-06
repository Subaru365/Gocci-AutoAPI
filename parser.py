
# Lib imports
import sys
import re

# Own imports
from types import *
from util import *







def parseLineOrErrorOut(regex, line, emsg):
        so = re.search(regex, line)
        if so:
            return so 
        else:
            die(emsg + " does not correspond to regex: '"+regex+"'\nFailed on Line: '" + line + "'")


def parseUriLine(line):
    if line.startswith("PAR"):
        so = parseLineOrErrorOut(r'^\w\w\w\s+([a-z_]+)\s+"(.+)"$', line, "PARSING ERROR: PAR Parameter")
        return ParameterToken(so.group(1), so.group(2))
    elif line.startswith("RES"):
        so = parseLineOrErrorOut(r'^\w\w\w\s+([a-z_]+)\s+"(.+)"$', line, "PARSING ERROR: RES Response")
        return ResponseToken(so.group(1), so.group(2))
    elif line.startswith("ERR"):
        so = parseLineOrErrorOut(r'^\w\w\w\s+([A-Z_]+)\s+"(.+)"$', line, "PARSING ERROR: ERR Error")
        return ErrorToken(so.group(1), so.group(2))

def parseGlobalError(line):
    so = parseLineOrErrorOut(r'^\w\w\w\s+([A-Z_]+)\s+"(.+)"$', line, "PARSING ERROR: ERR Error")
    return ErrorToken(so.group(1), so.group(2))



# VERY tolerant, lenient, idiotic parser. We could do this more serious one day, with real token tree + error msgs
# but it is not really nesseccry now. Just keep in mind this is not a "real" parser...
def parse(infile, vmajor, vminor):
    with open(infile) as f:
        content = f.readlines()


    # ignore all lines that do not start with API, URI, ERR, RES or PAR
    cleanContend = filterForLinesStartingWith(content, r'(VER|API|URI|ERR|RES|PAR)')


    uris = []
    global_errors = []

    for line in cleanContend:
        if line.startswith("VER"):
            so = parseLineOrErrorOut(r'VER\s+(\d+)\.(\d+)$', line, "PARSING ERROR: VER Version definition" )
            if vmajor < int(so.group(1)) or ( vmajor == int(so.group(1)) and vminor < int(so.group(2))):
                die("ERROR: Parser version (" + VERSION + ") too low for AAA file ("+ so.group(1) +"."+ so.group(2)+")")
            else:
                msg("AAA File version: " + so.group(1) +"."+ so.group(2))
        elif line.startswith("API"):
            pass

        elif line.startswith("URI"):
            so = parseLineOrErrorOut(r'URI\s+(/[a-z_/]+)$', line, "PARSING ERROR: URI definition" )
            uris.append(URIToken(so.group(1)))
            msg("Parsing URI: "+ so.group(1))

        elif line.startswith("PAR"):
            if not uris :
                die("PARSING ERROR: No parameter definitions in global space allowed. (define them in an URI space)\nERROR Line: " + line)
            uris[-1].addParameter(parseUriLine(line))

        elif line.startswith("RES"):
            if not uris :
                die("PARSING ERROR: No response definitions in global space allowed. (define them in an URI space)\nERROR Line: " + line)
            uris[-1].addResponse(parseUriLine(line))
        elif line.startswith("ERR"):
            if not uris :
                # global erros
                global_errors.append(parseGlobalError(line))
            else:
                # URI specific errors
                uris[-1].addError(parseUriLine(line))

    for uri in uris:
        uri.autoGenerateMalformErrors()

    for ge in global_errors:
        print(ge)

    for uri in uris:
        print(uri)





