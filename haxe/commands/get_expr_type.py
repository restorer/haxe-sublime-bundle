import sublime, sublime_plugin
import os
import re
import json
import codecs
import functools

from sublime import Region


from haxe.plugin import is_st3, is_st2

import haxe.tools.view as viewtools
import haxe.project as hxproject
import haxe.codegen as hxcodegen
import haxe.tools.path as pathtools
import haxe.hxtools as hxsrctools
import haxe.settings as hxsettings
import haxe.completion.hx.constants as hxcc
import haxe.tools.view as viewtools
import haxe.temp as hxtemp

from haxe.log import log
from haxe.completion.hx.types import CompletionOptions
from haxe.completion.hx.base import trigger_completion

class HaxeGetTypeOfExprCommand (sublime_plugin.TextCommand ):
    def run( self , edit ) :
        

        view = self.view
        
        file_name = view.file_name()

        if file_name == None:
            return

        file_name = os.path.basename(view.file_name())

        window = view.window()
        folders = window.folders()
 
        project_dir = folders[0]
        tmp_folder = folders[0] + "/tmp"
        target_file = folders[0] + "/tmp/" + file_name

        if os.path.exists(tmp_folder):
            pathtools.remove_dir(tmp_folder)           
        

        os.makedirs(tmp_folder)
        

        fd = open(target_file, "w+")
        sel = view.sel()

        word = view.substr(sel[0])

        replacement = "(hxsublime.Utils.getTypeOfExpr(" + word + "))."

        newSel = Region(sel[0].a, sel[0].a + len(replacement))


        view.replace(edit, sel[0], replacement)

        newSel = view.sel()[0]

        view.replace(edit, newSel, word)

        new_content = view.substr(sublime.Region(0, view.size()))
        fd.write(new_content)

        view.run_command("undo")

    