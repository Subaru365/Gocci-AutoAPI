#!/usr/bin/env python

# Lib imports
import sys
import getopt
import re

# Own imports
from types import *
from util import *


VERSION_MAJOR=3
VERSION_MINOR=3
VERSION = str(VERSION_MAJOR) + "." + str(VERSION_MINOR)

SourceTarget = Enum(["SWIFT", "JAVA", "PHP"])




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
    # with error code

    so = parseLineOrErrorOut(r'^\w\w\w\s+(\d\d\d)?\s+([A-Z_]+)\s+"(.+)"$', line, "PARSING ERROR: ERR Error")
    # print("MATCH 1: " + so.group(1) if so.group(1) else "NONE")
    # print("MATCH 2: " + so.group(2) if so.group(2) else "NONE")
    # print("MATCH 3: " + so.group(3) if so.group(3) else "NONE")
    
    # with custom error code
    if so.group(1):
        return ErrorToken(so.group(2), so.group(3), so.group(1))

    return ErrorToken(so.group(2), so.group(3))



# VERY tolerant, lenient, idiotic parser. We could do this more serious one day, with real token tree + error msgs
# but it is not really nesseccry now. Just keep in mind this is not a "real" parser...
def parse(infile):
    with open(infile) as f:
        content = f.readlines()


    # ignore all lines that do not start with API, URI, ERR, RES or PAR
    cleanContend = filterForLinesStartingWith(content, r'(VER|API|URI|ERR|RES|PAR)')


    uris = []
    global_errors = []
    version_major = 0 
    version_minor = 0 

    for line in cleanContend:
        if line.startswith("VER"):
            so = parseLineOrErrorOut(r'VER\s+(\d+)\.(\d+)$', line, "PARSING ERROR: VER Version definition" )
            if VERSION_MAJOR < int(so.group(1)) or ( VERSION_MAJOR == int(so.group(1)) and VERSION_MINOR < int(so.group(2))):
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
        uri.setErrorCodesAscending()

    # uniq error codes for every non set global error
    next_error_code = 200
    used_error_codes = set()
    for gerror in global_errors:
        if gerror.code:
            used_error_codes.add(int(gerror.code))
    for gerror in global_errors:
        if gerror.code == None:
            while next_error_code in used_error_codes:
                next_error_code += 1
            gerror.code = str(next_error_code)
            used_error_codes.add(next_error_code)



    for ge in global_errors:
        print(ge)

    for uri in uris:
        print(uri)




#########################################################################################
#########################################################################################

def usage():                         
    msg("Usage:\n\tparser.py [--help] [--swift | --java | --php] [input] [output]")
    msg("\n\tOne and only one source format has to be defined.")
    msg("\tDefault input  filename: api.aaa")
    msg("\tDefault output filename: <stdout>")

def main(argv):                         
    try:
        opts, args = getopt.getopt(argv, "sjph", ["swift", "java", "php", "help"])
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    source_target=None

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit()
        elif opt in ("-s", "--swift"):
            source_target=SourceTarget.SWIFT
        elif opt in ("-j", "--java"):
            source_target=SourceTarget.JAVA
        elif opt in ("-p", "--php"):
            source_target=SourceTarget.PHP

    if not source_target:
        usage()
        sys.exit(2)

    print(args)

    input_filename = args[0] if len(args) >= 1 else "api.aaa"
    output_filename = args[1] if len(args) >= 2 else "<STDOUT>"

    msg("Generate source code in: " + source_target)
    msg("Input  file: " + input_filename )
    msg("Output file: " + output_filename + "\n\n")

    token_tree = parse(input_filename)

    # if source_target == SourceTarget.SWIFT:
        # source = generate_swift(token_tree)
    # elif source_target == SourceTarget.JAVA:
        # source = generate_java(token_tree)
    # elif source_target == SourceTarget.PHP
        # source = generate_php(token_tree)

    # write_output(source, output_filename)



if __name__ == "__main__":
    msg("Automatic API interface class generator. (Version: " + VERSION + ")")
    main(sys.argv[1:])
