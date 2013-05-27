import sublime

is_st3 = int(sublime.version()) >= 3000

if is_st3:
	import Haxe.haxe.settings as hxsettings
else:
	import haxe.settings as hxsettings

def log (msg):
	if hxsettings.use_debug_panel():
		if is_st3:
			import Haxe.haxe.panel as hxpanel
		else:
			import haxe.panel as hxpanel
		def f():
			hxpanel.debug_panel().writeln(str(msg))
		sublime.set_timeout(f, 100)