import sublime

from haxe.plugin import is_st3, is_st2
import haxe.settings as hxsettings


# debug should only be used for internal debugging
# currently it's the same as log but this should change in the future (2 levels (debug, log))
def debug(msg):
	log(msg, False)

def log (msg, to_file = False):
	if to_file:
		f = codecs.open( "st3_haxe_log.txt" , "wb" , "utf-8" , "ignore" )
		f.append( str(msg) + "\n" )
		f.close()
	else:
		if hxsettings.use_debug_panel():
			import haxe.panel as hxpanel
			def f():
				hxpanel.debug_panel().writeln(str(msg))
			sublime.set_timeout(f, 100)