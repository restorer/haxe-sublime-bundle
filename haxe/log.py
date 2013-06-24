import sublime

import codecs

from haxe.tools.stringtools import encode_utf8




# debug should only be used for internal debugging
# currently it's the same as log but this should change in the future (2 levels (debug, log))
def debug(msg):
	log(msg, False)

def log (msg, to_file = False):
	if isinstance(msg, list):
		msg = ",".join(msg)
	if to_file:
		f = codecs.open( "st3_haxe_log.txt" , "wb" , "utf-8" , "ignore" )
		f.append( encode_utf8(msg) + "\n" )
		f.close()
	else:
		from haxe import settings
		from haxe import panel as hxpanel
		
		if settings.use_debug_panel():
			
			def f():
				hxpanel.debug_panel().writeln(encode_utf8(msg))
			sublime.set_timeout(f, 100)
		else:
			try:
				print(encode_utf8(msg))
			except:
				pass