import sublime, sublime_plugin
import json

from haxe import panel

from haxe.commands.find_declaration import HaxeFindDeclarationCommand

from haxe.log import log


class HaxeShowDocCommand( HaxeFindDeclarationCommand ):

    def helper_method(self):
        return "hxsublime.FindDeclaration.__sublimeShowDoc"


    def handle_successfull_result(self, view, json_res, using_insert, insert_before, insert_after, expr_end, build, temp_path, temp_file):
        if "doc" in json_res.keys() :
        	doc = json_res["doc"]
        else :
        	doc = "No documentation found"
        #log("json: " + str(json_res))
        #log("doc: " + str(doc))
        panel.slide_panel().writeln(msg=doc, show_timestamp=False)

