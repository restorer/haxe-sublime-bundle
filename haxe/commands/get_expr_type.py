import sublime, sublime_plugin
import os
from sublime import Region

from haxe.tools import pathtools

from haxe import panel

from haxe.commands.find_declaration import HaxeFindDeclarationCommand

# TODO this is currently not working

class HaxeGetTypeOfExprCommand (HaxeFindDeclarationCommand ):
    def helper_method(self):
        return "hxsublime.FindDeclaration.__getType"
        

    def handle_successfull_result(self, view, json_res, using_insert, insert_before, insert_after, expr_end, build, temp_path, temp_file):
        t = json_res["type"]
        e = json_res["expr"]
        
        msg = "Expr: " + e + "\n" + "Type: " + t

        panel.slide_panel().writeln(msg=msg, show_timestamp=False)
    