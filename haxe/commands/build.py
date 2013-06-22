
import sublime, sublime_plugin
from haxe.tools import viewtools
from haxe import project as hxproject
from haxe import settings
from haxe.log import log


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

        if project.has_build():
            project.run_sublime_build( view )
        else:
            log("no builds selected")
            project.extract_build_args(view, True);

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
                if (settings.check_on_save()):
                    project = hxproject.current_project(view)
                
                    if project.has_build():
                        project.check_build( view )
                        

