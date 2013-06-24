import sublime, sublime_plugin
import functools

from haxe import project as hxproject
from haxe.log import log


class HaxeInstallLibCommand( sublime_plugin.WindowCommand ):

    def run(self):

        view = sublime.active_window().active_view()

        project = hxproject.current_project(view)

        if project is not None:
            manager = project.haxelib_manager
            libs = manager.search_libs()
            menu = self._prepare_menu(libs, manager)
            on_selected = functools.partial(self._entry_selected, libs, manager)
            self.window.show_quick_panel(menu, on_selected)

    def _prepare_menu (self, libs, manager):
        menu = []
        for l in libs :
            if manager.is_lib_installed(l):
                menu.append( [ l + " [" + manager.get_lib(l).version + "]" , "Remove" ] )
            else :
                menu.append( [ l , 'Install' ] )

        menu.append( ["Upgrade libraries", "Upgrade installed libraries"] )
        menu.append( ["Haxelib Selfupdate", "Updates Haxelib itself"] )
        
        return menu

    def _entry_selected( self, libs, manager, i ):

        log("install lib command selected " + str(i))
        if i < 0 :
            return
        if i == len(libs) :
            log("upgrade all")
            manager.upgrade_all()
            
        if i == len(libs)+1 :
            log("self update")
            manager.self_update()
        else :
            lib = libs[i]
            if lib in manager.available :
                log("remove " + lib)
                manager.remove_lib(lib)
            else :
                log("install " + lib)
                manager.install_lib(lib)
