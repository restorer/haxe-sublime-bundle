import re

def startswith_any (s, list_str):
	for s1 in list_str:
		if s.startswith(s1):
			return True
	return False

def reverse (s):
	return s[::-1]



_whitespace = re.compile("^\s*$")

def is_whitespace_or_empty(s):
	return re.match(_whitespace, s) is not None