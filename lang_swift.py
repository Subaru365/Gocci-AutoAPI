

import types
import textwrap


# test_if_regex_matches = """
# func matches(s:String, p:String) -> Bool {
    # let regex = NSRegularExpression(pattern:p, 
				# options: nil, 
				# error: nil)!
	# let matcheCnt = regex.numberOfMatchesInString(s, 
				# options: nil, 
				# range: NSMakeRange(0, s.length))
	# return matcheCnt > 0
# b}
# """



class SwiftUtil 

    def ident(code):
        return "    " + code.replace('\n', '\n    ')

    def wrapInClass(classname, code):
        return "class {} {\n{}\n}".format(classname, code)
     
    def generateRegExCheck(inputVariableName, regex)

class SwiftGenerator(


class SwiftParameter : ParameterToken
    
    def generateRegExTest()
        code = textwrap.dedent(
        """
        """
)) 

test_if_regex_matches = """
func matches(s:String, p:String) -> Bool {
    let regex = NSRegularExpression(pattern:p, 
				options: nil, 
				error: nil)!
	let matcheCnt = regex.numberOfMatchesInString(s, 
				options: nil, 
				range: NSMakeRange(0, s.length))
	return matcheCnt > 0
b}
""".format(


