def startswith_any (s, list_str):
	for s1 in list_str:
		if s.startswith(s1):
			return True
	return False

def reverse (s):
	return s[::-1]