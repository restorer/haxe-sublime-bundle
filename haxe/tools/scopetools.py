def contains_any (scopes, scopes_test):
	for s in scopes : 
		if s.split(".")[0] in scopes_test : 
			return True
	return False

def contains_string_or_comment (scopes):
	return contains_any(scopes, ["string", "comments"])
