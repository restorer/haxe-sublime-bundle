import re

compact_func = re.compile("\(.*\)")
compact_prop = re.compile(":.*\.([a-z_0-9]+)", re.I)
space_chars = re.compile("\s")
word_chars = re.compile("[a-z0-9._]", re.I)
import_line = re.compile("^([ \t]*)import\s+([a-z0-9._]+);", re.I | re.M)
using_line = re.compile("^([ \t]*)using\s+([a-z0-9._]+);", re.I | re.M)
package_line = re.compile("package\s*([a-z0-9.]*);", re.I)

type_decl_with_scope = re.compile("(private\s+)?(?:extern\s+)?(class|typedef|enum|typedef|abstract)\s+([A-Z][a-zA-Z0-9_]*)\s*(<[a-zA-Z0-9_,]+>)?" , re.M )

type_decl = re.compile("(class|typedef|enum|typedef|abstract)\s+([A-Z][a-zA-Z0-9_]*)\s*(<[a-zA-Z0-9_,]+>)?" , re.M )

enum_start_decl = re.compile("enum\s+([A-Z][a-zA-Z0-9_]*)\s*(<[a-zA-Z0-9_,]+>)?" , re.M )

skippable = re.compile("^[a-zA-Z0-9_\s]*$")
in_anonymous = re.compile("[{,]\s*([a-zA-Z0-9_\"\']+)\s*:\s*$" , re.M | re.U )

variables = re.compile("var\s+([^:;\s]*)", re.I)
functions = re.compile("function\s+([^;\.\(\)\s]*)", re.I)
named_functions = re.compile("function\s+([a-zA-Z0-9_]+)\s*\(", re.I)
function_params = re.compile("function\s+[a-zA-Z0-9_]+\s*\(([^\)]*)", re.M)
param_default = re.compile("(=\s*\"*[^\"]*\")", re.M)
is_type = re.compile("^[A-Z][a-zA-Z0-9_]*$")
comments = re.compile("(//[^\n\r]*?[\n\r]|/\*(.*?)\*/)", re.MULTILINE | re.DOTALL )



def search_next_char_on_same_nesting_level (hx_src_section, char, start_pos):
	open_pars = 0
	open_braces = 0
	open_brackets = 0
	open_angle_brackets = 0

	count = len(hx_src_section)
	cur = ""
	pos = start_pos
	while (True):
		if pos > count-1:
			break

		c = hx_src_section[pos]

		next = hx_src_section[pos+1] if pos < count-1 else None

		if (c == char and open_pars == 0 and open_braces == 0 and open_brackets == 0 and open_angle_brackets == 0):
			return (pos,cur)
						
		if (c == "-" and next == ">"):
			cur += "->"
			pos += 2
		elif (c == "{"):
			pos += 1
			open_braces += 1
			cur += c
		elif (c == "}"):
			pos += 1
			open_braces -= 1
			cur += c
		elif (c == "("):
			pos += 1
			open_pars += 1
			cur += c
		elif (c == ")"):
			pos += 1
			open_pars -= 1
			cur += c
		elif (c == "["):
			pos += 1
			open_brackets += 1
			cur += c
		elif (c == "]"):
			pos += 1
			open_brackets -= 1
			cur += c
		elif (c == "<"):
			pos += 1
			open_angle_brackets += 1
			cur += c
		elif (c == ">"):
			pos += 1
			open_angle_brackets -= 1
			cur += c
		else:
			pos += 1
			cur += c
	return None

def reverse_search_next_char_on_same_nesting_level (hx_src_section, char, start_pos):
	open_pars = 0
	open_braces = 0
	open_brackets = 0
	open_angle_brackets = 0

	
	cur = ""
	pos = start_pos
	while (True):
		if pos <= -1:
			break

		c = hx_src_section[pos]

		next = hx_src_section[pos-1] if pos > 0 else None

		if (c == char and open_pars == 0 and open_braces == 0 and open_brackets == 0 and open_angle_brackets == 0):
			return (pos,cur)
						
		if (c == ">" and next == "-"):
			cur = "->" + cur
			pos -= 2
		elif (c == "}"):
			pos -= 1
			open_braces += 1
			cur = c + cur
		elif (c == "{"):
			pos -= 1
			open_braces -= 1
			cur = c + cur
		elif (c == ")"):
			pos -= 1
			open_pars += 1
			cur = c + cur
		elif (c == "("):
			pos -= 1
			open_pars -= 1
			cur = c + cur
		elif (c == "]"):
			pos -= 1
			open_brackets += 1
			cur = c + cur
		elif (c == "["):
			pos -= 1
			open_brackets -= 1
			cur = c + cur
		elif (c == ">"):
			pos -= 1
			open_angle_brackets += 1
			cur = c + cur
		elif (c == "<"):
			pos -= 1
			open_angle_brackets -= 1
			cur = c + cur
		else:
			pos -= 1
			cur = c + cur
	return None