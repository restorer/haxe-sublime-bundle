import sublime



is_st3 = int(sublime.version()) >= 3000

def plugin_unloaded_handler():
	import haxe.project as hxproject
	
	print("destroy")
	#hxproject.destroy()
	
import atexit
atexit.register(plugin_unloaded_handler)

if is_st3:
	def plugin_unloaded():
		plugin_unloaded_handler()
else:
	def unload_handler():
		plugin_unloaded_handler()
