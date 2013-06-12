import sublime

import re

from haxe.plugin import is_st3, is_st2


import haxe.lib as hxlib



lib_flag = re.compile("-lib\s+(.*?)")


def auto_complete( project, view , offset, prefix ) :
    src = view.substr(sublime.Region(0, offset))
    current_line = src[src.rfind("\n")+1:offset]
    m = lib_flag.match( current_line )
    if m is not None :
        return hxlib.HaxeLib.get_completions()
    else :
        return []
