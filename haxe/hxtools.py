import re

compactFunc = re.compile("\(.*\)")
compactProp = re.compile(":.*\.([a-z_0-9]+)", re.I)
spaceChars = re.compile("\s")
wordChars = re.compile("[a-z0-9._]", re.I)
importLine = re.compile("^([ \t]*)import\s+([a-z0-9._]+);", re.I | re.M)
usingLine = re.compile("^([ \t]*)using\s+([a-z0-9._]+);", re.I | re.M)
packageLine = re.compile("package\s*([a-z0-9.]*);", re.I)

typeDecl = re.compile("(class|typedef|enum|typedef|abstract)\s+([A-Z][a-zA-Z0-9_]*)\s*(<[a-zA-Z0-9_,]+>)?" , re.M )
skippable = re.compile("^[a-zA-Z0-9_\s]*$")
inAnonymous = re.compile("[{,]\s*([a-zA-Z0-9_\"\']+)\s*:\s*$" , re.M | re.U )

variables = re.compile("var\s+([^:;\s]*)", re.I)
functions = re.compile("function\s+([^;\.\(\)\s]*)", re.I)
functionParams = re.compile("function\s+[a-zA-Z0-9_]+\s*\(([^\)]*)", re.M)
paramDefault = re.compile("(=\s*\"*[^\"]*\")", re.M)
isType = re.compile("^[A-Z][a-zA-Z0-9_]*$")
comments = re.compile("(//[^\n\r]*?[\n\r]|/\*(.*?)\*/)", re.MULTILINE | re.DOTALL )
