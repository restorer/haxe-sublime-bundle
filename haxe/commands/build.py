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

class HaxeSaveAllAndRunCommand( sublime_plugin.TextCommand ):
    def run( self , edit ) :
        log("run HaxeSaveAllAndBuildCommand")
        view = self.view
        view.window().run_command("save_all")
        hxproject.current_project(self.view).run_build( view )

class HaxeSaveAllAndCheckCommand( sublime_plugin.TextCommand ):
    def run( self , edit ) :
        log("run HaxeSaveAllAndBuildCommand")
        view = self.view
        view.window().run_command("save_all")
        hxproject.current_project(self.view).check_build( view )

class HaxeSaveAllAndBuildCommand( sublime_plugin.TextCommand ):
    def run( self , edit ) :
        log("run HaxeSaveAllAndBuildCommand")
        view = self.view
        view.window().run_command("save_all")
        hxproject.current_project(self.view).just_build( view )

class HaxeRunBuildCommand( sublime_plugin.TextCommand ):
    def run( self , edit ) :
        view = self.view
        log("run HaxeRunBuildCommand")
        project = hxproject.current_project(self.view)

        if len(project.builds) == 0:
            log("no builds available")
            project.extract_build_args(view, True);
        else:
            project.run_sublime_build( view )


class HaxeSelectBuildCommand( sublime_plugin.TextCommand ):
    def run( self , edit ) :
        log("run HaxeSelectBuildCommand")
        view = self.view
        
        hxproject.current_project(self.view).select_build( view )



class HaxeBuildOnSaveListener ( sublime_plugin.EventListener ):
    def on_post_save(self, view):
        log("on_post_save")
        if view is not None and view.file_name() is not None:
            if viewtools.is_supported(view) or view.file_name().endswith(".erazor.html"):
                if (hxsettings.build_on_save()):
                    project = hxproject.current_project(view)
                
                    if len(project.builds) > 0:
                        project.check_build( view )
                    else:
                        project.extract_build_args(view, False)
                        build = project.get_build(view)
                        if (build != None):
                            project.check_build( view )

