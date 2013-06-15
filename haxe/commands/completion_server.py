import sublime, sublime_plugin
import os
import re
import functools

from haxe import project as hxproject

from haxe.log import log

class HaxeRestartServerCommand( sublime_plugin.WindowCommand ):

    def run( self ) : 
        log("run HaxeRestartServerCommand")
        
        view = sublime.active_window().active_view()
        
        project = hxproject.current_project(view)

        project.restart_server( view )
        