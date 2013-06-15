import sublime_plugin

from haxe import codegen

from haxe.log import log

class HaxeGenerateUsingCommand( sublime_plugin.TextCommand ):
    def run( self , edit ) :
        log("run HaxeGenerateUsingCommand")
        codegen.generate_using(self.view, edit)
        
class HaxeGenerateImportCommand( sublime_plugin.TextCommand ):
    def run( self, edit ) :
        log("run HaxeGenerateImportCommand")
        codegen.generate_import(self.view, edit)
