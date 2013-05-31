import sublime
import os

def is_st3():
	return int(sublime.version()) >= 3000

def is_st2():
	return int(sublime.version()) < 3000


def plugin_base_dir():
	return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


print("IS SUBLIME TEXT 3: " + str(is_st3()))