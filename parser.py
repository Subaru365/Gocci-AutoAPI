
# Lib imports
import sys
import re
import itertools

# Own imports
from types import *
from util import *





def filterForLinesStartingWith(dirtyContend, filterRegEx):
    res = []
    for line in dirtyContend:
        if re.match(filterRegEx, line):
            res.append(line.strip())
    return res


def parseLineOrErrorOut(regex, line, emsg):
        so = re.search(regex, line)
        if so:
            return so 
        else:
            die(emsg + " does not correspond to regex: '"+regex+"'\nFailed on Line: '" + line + "'")

def parseParameterLine(line):
    so = parseLineOrErrorOut(r'^PAR\s+(OPT\s+)?([a-z_]+)\s+"(.+)"$', line, "PARSING ERROR: PAR Parameter")
    return ParameterToken(key = so.group(2), re = so.group(3), optional = so.group(1) != None)

def parseErrorLine(line):
    so = parseLineOrErrorOut(r'^\w\w\w\s+([A-Z_]+)\s+"(.+)"$', line, "PARSING ERROR: ERR Error")
    return ErrorToken(so.group(1), so.group(2))

def parseGlobalError(line):
    so = parseLineOrErrorOut(r'^\w\w\w\s+([A-Z_]+)\s+"(.+)"$', line, "PARSING ERROR: ERR Error")
    return ErrorToken(so.group(1), so.group(2))

def parseAPIDictLine(line, apidict):
    so = parseLineOrErrorOut(r'^API\s+"([a-zA-Z0-9_]+)"\s+"(.+)"$', line, "PARSING ERROR: ERR Error")
    apidict.addPair(so.group(1), so.group(2))


def parseResponseLine(firstline, lineiterator, level=1):
    if firstline.startswith("RES ARRAY"):
        return parseResponseArrayPre(firstline, lineiterator, level)
    if firstline.startswith("RES DICT"):
        return parseResponseDictonary(firstline, lineiterator, level)
    elif firstline.startswith("RES"):
        return parseResponseSimple(firstline)
    else:
        die("PARSING ERROR: Response parsing failed on deepest level. This is not valid:\nERROR Line: " + firstline)

def parseResponseSimple(line):
        # so = parseLineOrErrorOut(r'^\w\w\w\s+([a-z_]+)\s+"(.+)"$', line, "PARSING ERROR: RES Response")
        so = parseLineOrErrorOut(r'^\w\w\w\s+([a-z_]+)\s+(BOOLEAN|FLOAT|INTEGER|".+")$', line, "PARSING ERROR: RES Response")
        if so.group(2) == "INTEGER":
            return ResponseToken(so.group(1), None, typ=ResponseType.INTEGER)
        elif so.group(2) == "FLOAT":
            return ResponseToken(so.group(1), None, typ=ResponseType.FLOAT)
        elif so.group(2) == "BOOLEAN":
            return ResponseToken(so.group(1), None, typ=ResponseType.BOOLEAN)
        else:
            return ResponseToken(so.group(1), so.group(2), typ=ResponseType.STRING)

def parseResponseArray(line):
    so = parseLineOrErrorOut(r'^RES\s+ARRAY\s+OF\s+([a-z_]+)\s+"(.+)"$', line, "PARSING ERROR: RES Response")
    return ResponseArrayToken(so.group(1), so.group(2))

def parseResponseArrayCompound(firstline, iterator, level=1):
    arrayname = parseLineOrErrorOut(r'^RES\s+ARRAY\s+([a-z_]+)$', firstline, "PARSING ERROR: RES ARRAY Response").group(1)
    res = ResponseArrayCompoundToken(arrayname, level)
    for nextline in iterator:
        if nextline.startswith("RES ARRAY END"):
            return res
        elif nextline.startswith("RES ARRAY"):
            res.add(parseResponseArrayCompound(nextline, iterator, level+1))
        elif nextline.startswith("RES"):
            res.add(parseResponseLine(nextline, iterator, level))
        else:
            die("PARSING ERROR: Only RES and RES ARRAY definitions are allowed in an array space\nERROR Line: " + nextline)
    die("PARSING ERROR: Array definition did not end in 'RES ARRAY END'\nERROR Line: " + firstline)


def parseResponseArrayPre(firstline, lineiter, level=1):
    if firstline.startswith("RES ARRAY END"):
        die("PARSING ERROR: JESUS!? Don't mix array and dict definitions. Do you want json like: [ { ] } or what?\nERROR Line: " + firstline)
    elif firstline.startswith("RES ARRAY OF"):
        return parseResponseArray(firstline)
    else:
        return parseResponseArrayCompound(firstline, lineiter, level)

def parseResponseDictonary(firstline, iterator, level=1):
    dictname = parseLineOrErrorOut(r'^RES\s+DICT\s+([a-z_]+)$', firstline, "PARSING ERROR: RES DICT Response").group(1)
    res = ResponseDictonaryToken(dictname, level)
    for line in iterator:
        if line.startswith("RES DICT END"):
            return res
        elif line.startswith("RES DICT"):
            res.add(parseResponseDictonary(line, iterator, level+1))
        elif line.startswith("RES ARRAY"):
            res.add(parseResponseArrayPre(line, iterator))
        elif line.startswith("RES"):
            res.add(parseResponseLine(line, iterator, level))
        else:
            die("PARSING ERROR: Only RES definitions are allowed in a dictonary space\nERROR Line: " + line)
    die("PARSING ERROR: Dictonary definition did not end in 'RES DICT END'\nERROR Line: " + firstline)

# yes this is a little bit hacky 
def parseResponseDictonaryTopLevel(allLines):
    toparse = []
    while len(allLines) != 0:
        if allLines[-1].startswith("RES"):
            toparse.append(allLines.pop())
        else:
            break
    toparse.append("RES DICT END")
    return parseResponseDictonary("RES DICT payload", iter(toparse))


# VERY tolerant, lenient, idiotic parser. We could do this more serious one day, with real token tree + error msgs
# but it is not really nesseccry now. Just keep in mind this is not a "real" parser...
def parse(infile, vmajor, vminor):
    with open(infile) as f:
        content = f.readlines()


    # ignore all lines that do not start with VER, API, URI, ERR, RES or PAR
    cleanContend = filterForLinesStartingWith(content, r'\s*(VER|API|URI|ERR|RES|PAR)')

    cleanContend = list(reversed(cleanContend))
    
    uris = []
    global_errors = []
    apidict = APIDict()
    aaaversion = None 

    while not len(cleanContend) == 0:
        line = cleanContend.pop()

        if line.startswith("VER"):
            so = parseLineOrErrorOut(r'VER\s+(\d+)\.(\d+)$', line, "PARSING ERROR: VER Version definition" )
            if vmajor < int(so.group(1)) or ( vmajor == int(so.group(1)) and vminor < int(so.group(2))):
                die("ERROR: Parser version (" + VERSION + ") too low for AAA file ("+ so.group(1) +"."+ so.group(2)+")")
            else:
                msg("AAA File version: " + so.group(1) +"."+ so.group(2))
                aaaversion = so.group(1) +"."+ so.group(2)

        elif line.startswith("API"):
            parseAPIDictLine(line, apidict)

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
            uris[-1].addParameter(parseParameterLine(line))

        elif line.startswith("RES"):
            if not uris :
                die("PARSING ERROR: No response definitions in global space allowed. (define them in an URI space)\nERROR Line: " + line)

            cleanContend.append(line)
            uris[-1].setResponseTree(parseResponseDictonaryTopLevel(cleanContend))

        elif line.startswith("ERR"):
            if not uris :
                # global erros
                global_errors.append(parseGlobalError(line))
            else:
                # URI specific errors
                uris[-1].addError(parseErrorLine(line))

    if aaaversion == None:
        die("The AAA file must contain a version definition in the form of 'VER X.Y'")

    for uri in uris:
        uri.autoGenerateMalformErrors()

    return Everything(aaaversion, apidict, global_errors, uris)





