import sublime

def log (msg):
	import haxe.panel as hxpanel
	def f():
		hxpanel.debug_panel().writeln(str(msg))
	sublime.set_timeout(f, 100)