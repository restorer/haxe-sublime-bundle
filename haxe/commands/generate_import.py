import sublime, sublime_plugin

import haxe.project as hxproject

import haxe.codegen as hxcodegen

from haxe.log import log


class HaxeGenerateUsingCommand( sublime_plugin.TextCommand ):
    def run( self , edit ) :
        log("run HaxeGenerateUsingCommand")
        hxcodegen.generate_using(self.view, edit)
        


class HaxeGenerateImportCommand( sublime_plugin.TextCommand ):

    def run( self, edit ) :
        log("run HaxeGenerateImportCommand")
        hxcodegen.generate_import(self.view, edit)
        

