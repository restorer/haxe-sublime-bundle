import sublime

import codecs




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
		from haxe import settings
		from haxe import panel as hxpanel
		
		if settings.use_debug_panel():
			
			def f():
				hxpanel.debug_panel().writeln(str(msg))
			sublime.set_timeout(f, 100)