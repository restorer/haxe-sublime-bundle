import sublime

import re

is_st3 = int(sublime.version()) >= 3000

if is_st3:
	import Haxe.haxe.lib as hxlib
else:
	import haxe.lib as hxlib



lib_flag = re.compile("-lib\s+(.*?)")


def auto_complete( project, view , offset ) :
    src = view.substr(sublime.Region(0, offset))
    current_line = src[src.rfind("\n")+1:offset]
    m = lib_flag.match( current_line )
    if m is not None :
        return hxlib.HaxeLib.get_completions()
    else :
        return []
