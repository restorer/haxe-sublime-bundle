import re

compact_func = re.compile("\(.*\)")
compact_prop = re.compile(":.*\.([a-z_0-9]+)", re.I)
space_chars = re.compile("\s")
word_chars = re.compile("[a-z0-9._]", re.I)
import_line = re.compile("^([ \t]*)import\s+([a-z0-9._]+);", re.I | re.M)
using_line = re.compile("^([ \t]*)using\s+([a-z0-9._]+);", re.I | re.M)
package_line = re.compile("package\s*([a-z0-9.]*);", re.I)

type_decl = re.compile("(class|typedef|enum|typedef|abstract)\s+([A-Z][a-zA-Z0-9_]*)\s*(<[a-zA-Z0-9_,]+>)?" , re.M )
skippable = re.compile("^[a-zA-Z0-9_\s]*$")
in_anonymous = re.compile("[{,]\s*([a-zA-Z0-9_\"\']+)\s*:\s*$" , re.M | re.U )

variables = re.compile("var\s+([^:;\s]*)", re.I)
functions = re.compile("function\s+([^;\.\(\)\s]*)", re.I)
function_params = re.compile("function\s+[a-zA-Z0-9_]+\s*\(([^\)]*)", re.M)
param_default = re.compile("(=\s*\"*[^\"]*\")", re.M)
is_type = re.compile("^[A-Z][a-zA-Z0-9_]*$")
comments = re.compile("(//[^\n\r]*?[\n\r]|/\*(.*?)\*/)", re.MULTILINE | re.DOTALL )
