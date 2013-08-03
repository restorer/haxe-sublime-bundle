import sublime, sublime_plugin
import os
import sublime_plugin

from haxe.tools import viewtools

from haxe import project as hxproject
from haxe.tools import hxsrctools

from haxe.log import log

# TODO Cleanup this module


# stores the info for file creation, this data is shared between command and listener instances.
current_create_type_info = {}


class HaxeCreateTypeCommand( sublime_plugin.WindowCommand ):

    def __init__ (self, win):
        self.classpath = None
        self.win = win


    def run( self , paths = [] , t = "class" ) :
        log("createtype")
        
        win = self.win      
        view = win.active_view()

        project = hxproject.current_project(view)

        builds = list(project.builds)

        if project.has_build():
            builds.insert(0, project.get_build(view))

        pack = [];
        
        if len(builds) == 0 and view != None and view.file_name() != None:
            log(view.file_name())
            project.extract_build_args(view)
            builds = project.builds

        if len(paths) == 0 and view != None:
            fn = view.file_name()
            paths.append(fn)

        for path in paths :

            if os.path.isfile( path ) :
                path = os.path.dirname( path )

            if self.classpath is None :
                self.classpath = path

            for b in builds :
                log("build file: " + b.build_file)
                found = False
                for cp in b.classpaths :
                    log("class path: " + cp)
                    log("path: " + path)
                    if path.startswith( cp ) :
                        
                        self.classpath = path[0:len(cp)]
                        log("self.classpath: " + self.classpath)
                        
                        rel_path = path[len(cp):]
                        
                        if len(rel_path) == 0:
                            found = True
                        else:
                            sub_packs = rel_path.split(os.sep)
                            log("subpacks:" + str(sub_packs))
                            for p in sub_packs :
                                if "." in p : 
                                    break
                                elif p :
                                    pack.append(p)
                                   
                                    found = True
     
                    if found:
                        break
                if found:
                    break
                log("found: " + str(found))

        if self.classpath is None :
            if len(builds) > 0 :
                self.classpath = builds[0].classpaths[0]

        # so default text ends with .
        if len(pack) > 0 :
            pack.append("")
                        
        sublime.status_message( "Current classpath : " + self.classpath )
        win.show_input_panel("Enter "+t+" name : " , ".".join(pack) , lambda inp: self.on_done(inp, t) , self.on_change , self.on_cancel )

    def on_done( self , inp, cur_type ) :

        fn = self.classpath;
        parts = inp.split(".")
        pack = []

        while( len(parts) > 0 ):
            p = parts.pop(0)
            
            fn = os.path.join( fn , p )
            if hxsrctools.is_type.match( p ) : 
                cl = p
                break;
            else :
                pack.append(p)

        if len(parts) > 0 :
            cl = parts[0]

        fn += ".hx"

        src = "\npackage " + ".".join(pack) + ";\n\n"+cur_type+" "+cl+" " 
        if cur_type == "typedef" :
            src += "= "
        src += "{\n\n\t\n\n}"

        current_create_type_info[fn] = src

        sublime.active_window().open_file( fn )
 

    def on_change( self , inp ) :
        #sublime.status_message( "Current classpath : " + self.classpath )
        log( inp )

    def on_cancel( self ) :
        None


class HaxeCreateTypeListener( sublime_plugin.EventListener ):

    def on_load (self, view):
        can_create_file = view is not None and view.file_name() != None and view.file_name() in current_create_type_info and view.size() == 0
        
        if can_create_file:
            self.create_file(view)

    def create_file(self, view):
        
        data = current_create_type_info[view.file_name()];
        
        def run_edit(v, edit):
            v.insert(edit,0,data)
            v.end_edit(edit)
            sel = v.sel()
            sel.clear()
            pt = v.text_point(5,1)
            sel.add( sublime.Region(pt,pt) )

        viewtools.async_edit(view, run_edit)
