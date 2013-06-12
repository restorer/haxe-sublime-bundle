import sublime
import os


is_st3 = int(sublime.version()) >= 3000

is_st2 = int(sublime.version()) < 3000


def plugin_base_dir():
	return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


print("IS SUBLIME TEXT 3: " + str(is_st3))