
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

def parseBaseFrameLine(line, baseframe):
    so = parseLineOrErrorOut(r'^API\s+"([a-z_]+)"\s+"(.+)"$', line, "PARSING ERROR: ERR Error")
    baseframe.addPair(so.group(1), so.group(2))


def parseResponseArray(line, iterator, level=1):
    arrayname = parseLineOrErrorOut(r'^RES\s+ARRAY\s+([a-z_]+)$', line, "PARSING ERROR: RES ARRAY Response").group(1)
    res = ResponseArrayToken(arrayname, level)
    for nextline in iterator:
        msg(nextline)
        if nextline.startswith("RES ARRAY END"):
            return res
        elif nextline.startswith("RES ARRAY"):
            res.add(parseResponseArray(nextline, iterator, level+1))
        elif nextline.startswith("RES"):
            res.add(parseUriLine(nextline))
        else:
            die("PARSING ERROR: Only RES and RES ARRAY definitions are allowed in array space\nERROR Line: " + line)
    die("PARSING ERROR: Array definition did not end in 'RES ARRAY END'\nERROR Line: " + line)


# VERY tolerant, lenient, idiotic parser. We could do this more serious one day, with real token tree + error msgs
# but it is not really nesseccry now. Just keep in mind this is not a "real" parser...
def parse(infile, vmajor, vminor):
    with open(infile) as f:
        content = f.readlines()


    # ignore all lines that do not start with API, URI, ERR, RES or PAR
    cleanContend = filterForLinesStartingWith(content, r'\s*(VER|API|URI|ERR|RES|PAR)')
    
    for l in cleanContend:
        print(l)

    uris = []
    global_errors = []
    baseframe = BaseFrame()

    lineiterator = iter(cleanContend)

    for line in lineiterator:

        if line.startswith("VER"):
            so = parseLineOrErrorOut(r'VER\s+(\d+)\.(\d+)$', line, "PARSING ERROR: VER Version definition" )
            if vmajor < int(so.group(1)) or ( vmajor == int(so.group(1)) and vminor < int(so.group(2))):
                die("ERROR: Parser version (" + VERSION + ") too low for AAA file ("+ so.group(1) +"."+ so.group(2)+")")
            else:
                msg("AAA File version: " + so.group(1) +"."+ so.group(2))
        elif line.startswith("API"):
            parseBaseFrameLine(line, baseframe)

        elif line.startswith("URI"):
            so = parseLineOrErrorOut(r'URI\s+(/[a-z_/]+)$', line, "PARSING ERROR: URI definition" )
            for uri in uris:
                if uri.path == so.group(1):
                    die("PARSING ERROR: URI with path '" + so.group(1) + "' was already difined. You made a copy and paste error :)")
            uris.append(URIToken(so.group(1)))
            msg("Parsing URI: "+ so.group(1))

        elif line.startswith("PAR"):
            if not uris :
                die("PARSING ERROR: No parameter definitions in global space allowed. (define them in an URI space)\nERROR Line: " + line)
            uris[-1].addParameter(parseUriLine(line))

        elif line.startswith("RES"):
            if not uris :
                die("PARSING ERROR: No response definitions in global space allowed. (define them in an URI space)\nERROR Line: " + line)
            if line.startswith("RES ARRAY"):
                # uris[-1].addResponse(parseResponseArray(line, lineiterator))
                print(parseResponseArray(line, lineiterator))
            else:
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

    return Everything(baseframe, global_errors, uris)





