import sublime, sublime_plugin
import json

from haxe import panel

from haxe.commands.find_declaration import HaxeFindDeclarationCommand

from haxe.log import log


class HaxeShowDocCommand( HaxeFindDeclarationCommand ):




    def helper_method(self):
        return "__sublimeShowDoc"

    def using_class(self):
        return "hxsublime.FindDeclaration"


    


    def handle_successfull_result(self, view, json_res, add, using_line, word_end, build, temp_path, temp_file, use_display, inline_workaround):
        doc = json_res["doc"]
        #log("json: " + str(json_res))
        #log("doc: " + str(doc))
        panel.slide_panel().writeln("\n" + doc)


