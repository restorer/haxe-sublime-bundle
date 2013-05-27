import sublime


def is_st3():
	return int(sublime.version()) >= 3000

def is_st2():
	return int(sublime.version()) < 3000



print("IS SUBLIME TEXT 3: " + str(is_st3()))