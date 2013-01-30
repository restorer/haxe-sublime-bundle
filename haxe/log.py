import sublime

import haxe.settings as hxsettings

def log (msg):
	if hxsettings.use_debug_panel():
		import haxe.panel as hxpanel
		def f():
			hxpanel.debug_panel().writeln(str(msg))
		sublime.set_timeout(f, 100)