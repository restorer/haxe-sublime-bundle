# -*- coding: utf-8 -*-
import sublime
import os
import re
import sys

from haxe.plugin import is_st3, is_st2

from haxe import build as hxbuild
from haxe import panel as hxpanel
from haxe import types as hxtypes
from haxe import settings as hxsettings
from haxe import execute as hxexecute
from haxe import haxelib

from haxe.tools import viewtools
from haxe.tools import pathtools
from haxe.tools import hxsrctools

from haxe.compiler import server as hxserver

from haxe.log import log

from haxe.project.tools import get_window, haxe_file_regex

from haxe.project.completion_state import ProjectCompletionState


_classpath_line = re.compile("Classpath : (.*)")

_haxe_version = re.compile("haxe_([0-9]{3})",re.M)


class Project:
    def __init__(self, id, file, win_id, server_port):
    	
        self.completion_context = ProjectCompletionState()
        self._haxelib_manager = haxelib.HaxeLibManager(self)
        self.current_build = None
        self.selecting_build = False
        self.builds = []
        self.win_id = win_id
        
        self.server = hxserver.Server(server_port)
        
        self.project_file = file

        self.project_id = id
        if (self.project_file is not None):
            self.project_path = os.path.normpath(os.path.dirname(self.project_file))
        else:
            self.project_path = None

        self._update_compiler_info()

    @property
    def haxelib_manager (self):
        return self._haxelib_manager

    def project_dir (self, default):
        return self.project_path if self.project_path is not None else default
            

    def nme_exec (self, view = None):
        return [hxsettings.haxelib_exec(), "run", "nme"]

    def openfl_exec (self, view = None):
        return [hxsettings.haxelib_exec(), "run", "openfl"]

    def haxelib_exec (self, view = None):
        return [hxsettings.haxelib_exec()]

    def haxe_exec (self, view = None):
        haxe_exec = hxsettings.haxe_exec(view)
        if not os.path.isabs(haxe_exec) and haxe_exec != "haxe":
            cwd = self.project_dir(".")

            haxe_exec = os.path.normpath(os.sep.join(os.path.join(cwd, hxsettings.haxe_exec(view)).split("/")))
        return [haxe_exec]

    
    def haxe_env (self, view = None):
        return _haxe_build_env(self.project_dir("."))
    
    
    def start_server(self, view):
        cwd = self.project_dir(".")
        haxe_exec = self.haxe_exec(view)[0]
        
        env = self.haxe_env()
        
        self.server.start(haxe_exec, cwd, env=env)
    

    def restart_server (self, view):
        self.server.stop(lambda: self.start_server( view ) )

    def is_server_mode (self):
        return self.server_mode and hxsettings.use_haxe_servermode()

    def is_server_mode_for_builds (self):
        return self.is_server_mode() and hxsettings.use_haxe_servermode_for_builds()

    def generate_build(self, view):
        fn = view.file_name()
        
        is_hxml_build = lambda: isinstance(self.current_build, hxbuild.HxmlBuild)

        if self.current_build is not None and is_hxml_build() and fn == self.current_build.hxml and view.size() == 0 :
            def run_edit(v, e):
                hxml_src = self.current_build.make_hxml()
                v.insert(e,0,hxml_src)
                v.end_edit(e)

            viewtools.async_edit(view, run_edit)

    def select_build( self, view ) :
        scopes = view.scope_name(view.sel()[0].end()).split()
        
        if 'source.hxml' in scopes:
            view.run_command("save")

        self.extract_build_args( view , True )

    def extract_build_args( self, view = None , force_panel = False ) :

        if view == None:
            view = sublime.active_window().active_view()



        folders = self._get_folders(view)
        log(folders)
        
        self.builds = self._find_builds_in_folders(folders)
        
        num_builds = len(self.builds)

        view_build_id = view.settings().get("haxe-current-build-id")
        log("view_build_id:" + str(view_build_id))

        if view_build_id is not None and view_build_id < num_builds and not force_panel:
            self._set_current_build( view , int(view_build_id) )
        elif num_builds == 1:
            if force_panel : 
                sublime.status_message("There is only one build")
            self._set_current_build( view , int(0) )
        elif num_builds == 0 and force_panel :
            sublime.status_message("No build files found (e.g. hxml, nmml, xml)")
            self._create_new_hxml(view, folders[0])
        elif num_builds > 1 and force_panel :
            self._show_build_selection_panel(view)
        else:
            self._set_current_build( view , int(0) )

    def has_build (self):
        return self.current_build is not None

    def check_build(self, view):
        self._build(view, "check")

    def just_build(self, view):
        self._build(view, "build")
        
    def run_build( self, view ) :
        self._build(view, "run")

    def _update_compiler_info (self):
        bundle, ver, std_paths = _collect_compiler_info(self.haxe_exec(), self.project_path)

        #assume it's supported if no version available
        self.server_mode = ver is None or ver >= 209
        

        self.std_bundle = bundle
        self.std_paths = std_paths
        #self.std_packages = packs
        #self.std_classes = ["Void","String", "Float", "Int", "UInt", "Bool", "Dynamic", "Iterator", "Iterable", "ArrayAccess"]
        #self.std_classes.extend(classes)

    


    # TODO rewrite this function and make it understandable
    
    def _find_builds_in_folders(self, folders):
        builds = []
        for f in folders:
            builds.extend(hxbuild.find_hxml_projects(self, f))
            builds.extend(hxbuild.find_nme_projects(self, f))
            builds.extend(hxbuild.find_openfl_projects(self, f))
        return builds

    def _get_view_file_name (self, view):
        if view is None:
            view = sublime.active_window().active_view()
        return view.file_name()                

    def _get_current_window (self, view):
        return get_window(view)

    def _get_folders (self, view):
        win = self._get_current_window(view)
        folders = win.folders()
        return folders

    


    def _create_new_hxml (self, view, folder):
        win = sublime.active_window()
        f = os.path.join(folder,"build.hxml")

        self.current_build = None
        self.get_build(view)
        self.current_build.hxml = f

        #for whatever reason generate_build doesn't work without transient
        win.open_file(f,sublime.TRANSIENT)

        self._set_current_build( view , int(0) )

    def _show_build_selection_panel(self, view):
        
        buildsView = [[b.to_string(), os.path.basename(b.build_file) ] for b in self.builds]

        
        self.selecting_build = True
        sublime.status_message("Please select your build")
        
        def on_selected (i):
            self.selecting_build = False
            self._set_current_build(view, i)   

        win = sublime.active_window()
        win.show_quick_panel( buildsView , on_selected  , sublime.MONOSPACE_FONT )        

    def _set_current_build( self, view , id ) :
        
        log( "_set_current_build")
        
        if id < 0 or id >= len(self.builds) :
            id = 0
        
        if len(self.builds) > 0 :
            view.settings().set("haxe-current-build-id", id)
            self.current_build = self.builds[id]
            self.current_build.set_std_bundle(self.std_bundle)

            view.set_status("haxe-build",self.current_build.to_string())
            #hxpanel.default_panel().writeln( "build selected: " + self.current_build.to_string() )
        else:
            view.set_status("haxe-build","No build found/selected")
            #hxpanel.default_panel().writeln( "No build found/selected" )
            
    
    
    def _build(self, view, type = "run"):

        if view is None: 
            view = sublime.active_window().active_view()

        win = view.window()

        env = _haxe_build_env(self.project_dir("."))
        
        if self.has_build():
            build = self.get_original_build(view)
        else:
            self.extract_build_args(view)
            build = self.get_original_build(view)

        if type == "run": # build and run
            cmd, build_folder = build.prepare_run_cmd(self, self.is_server_mode_for_builds(), view)
        elif type == "build": # just build
            cmd, build_folder = build.prepare_build_cmd(self, self.is_server_mode_for_builds(), view)
        else: # only check for errors
            cmd, build_folder = build.prepare_check_cmd(self, self.is_server_mode(), view)
        
        
        escaped_cmd = build.escape_cmd(cmd)


        hxpanel.default_panel().writeln("running: " + " ".join(escaped_cmd))


        
        win.run_command("haxe_exec", {
            "cmd": cmd,
            "is_check_run" : type == "check",
            "working_dir": build_folder,
            "file_regex": haxe_file_regex,
            "env" : env
        })


    def clear_build( self ) :
        self.current_build = None
        self.completion_context.clear_completion()

    def destroy (self) :
        self.server.stop()


    # TODO rewrite this function and make it understandable
    def _create_default_build (self, view):
        fn = view.file_name()

        src_dir = os.path.dirname( fn )

        src = view.substr(sublime.Region(0, view.size()))
    
        build = hxbuild.HxmlBuild(None, None)
        build.target = "js"

        folder = os.path.dirname(fn)
        folders = view.window().folders()
        for f in folders:
            if f in fn :
                folder = f

        pack = []
        for ps in hxsrctools.package_line.findall( src ) :
            if ps == "":
                continue
                
            pack = ps.split(".")
            for p in reversed(pack) : 
                spl = os.path.split( src_dir )
                if( spl[1] == p ) :
                    src_dir = spl[0]

        cl = os.path.basename(fn)
        if is_st2:
            cl = cl.encode('ascii','ignore')
        cl = cl[0:cl.rfind(".")]

        main = pack[0:]
        main.append( cl )
        build.main = ".".join( main )

        build.output = os.path.join(folder,build.main.lower() + ".js")

        build.args.append( ("-cp" , src_dir) )

        build.args.append( ("-js" , build.output ) )

        build.hxml = os.path.join( src_dir , "build.hxml")
        return build

    def get_original_build( self, view ) :
        
        if self.current_build is None and view.score_selector(0,"source.haxe.2") > 0 :
            self.current_build = self._create_default_build(view)
           
        return self.current_build


    def get_build( self, view ) :
        return self.get_original_build(view).copy()


def _haxe_build_env (project_dir):
        
    lib_path = hxsettings.haxe_library_path()
    haxe_inst_path = hxsettings.haxe_inst_path()
    neko_inst_path = hxsettings.neko_inst_path()


    env = os.environ.copy()

    env_path = os.environ.copy()["PATH"]
    
    

    paths = []

    def do_encode(s):
        if is_st3:
            return s
        else:
            return s.encode(sys.getfilesystemencoding())

    if lib_path is not None:
        if pathtools.is_abs_path(lib_path):
            path = lib_path
        else:
            path = os.path.normpath(os.path.join(project_dir, lib_path))

        env["HAXE_LIBRARY_PATH"] = do_encode(os.sep.join(path.split("/")))
        env["HAXE_STD_PATH"] = do_encode(os.sep.join(path.split("/")))
    

    if haxe_inst_path is not None:
        if pathtools.is_abs_path(haxe_inst_path):
            path = haxe_inst_path
        else:
            path = os.path.normpath(os.path.join(project_dir, haxe_inst_path))
        
        env["HAXEPATH"] = do_encode(os.sep.join(path.split("/")))
        paths.append(do_encode(os.sep.join(path.split("/"))))

    if neko_inst_path is not None:
        path = os.path.normpath(os.path.join(project_dir, neko_inst_path))
        env["NEKO_INSTPATH"] = do_encode(os.sep.join(path.split("/")))
        paths.append(do_encode(os.sep.join(path.split("/"))))

    
    if len(paths) > 0:
        env["PATH"] = os.pathsep.join(paths) + os.pathsep + env_path

    
    log(str(env))
    return env


def _get_compiler_info_env (project_path):

    return _haxe_build_env(project_path)


def _collect_compiler_info (haxe_exec, project_path):
    env = _get_compiler_info_env(project_path)
    cmd = haxe_exec

    cmd.extend(["-main", "Nothing", "-v", "--no-output"])

    
    out, err = hxexecute.run_cmd( cmd, env=env )


    std_classpaths = _extract_std_classpaths(out)
    
    bundle = _collect_std_classes_and_packs(std_classpaths)
            
    ver = _extract_haxe_version(out)
    
    return (bundle, ver, std_classpaths)

def _extract_haxe_version (out):
    ver = re.search( _haxe_version , out )
    return int(ver.group(1)) if ver is not None else None


def _remove_trailing_path_sep(path):
    if len(path) > 1:
        last_pos = len(path)-1
        last_char = path[last_pos]
        if last_char == "/" or  last_char == "\\" or last_char == os.path.sep:
            path = path[0:last_pos]
    return path

def _is_valid_classpath(path):
    return len(path) > 1 and os.path.exists(path) and os.path.isdir(path)

def _extract_std_classpaths (out):
    m = _classpath_line.match(out)
        
    std_classpaths = []

    all_paths = m.group(1).split(";")
    ignored_paths = [".","./"]

    std_paths = set(all_paths) - set(ignored_paths) if m is not None else []
    
    for p in std_paths : 
        p = os.path.normpath(p)
        
        p = _remove_trailing_path_sep(p)

        if _is_valid_classpath(p):
            std_classpaths.append(p)

    return std_classpaths


def _collect_std_classes_and_packs(std_cps):
    bundle = hxsrctools.empty_type_bundle()
    for p in std_cps : 
        bundle1 = hxtypes.extract_types( p, [], [], 0, [], False )
        bundle = bundle.merge(bundle1)
        

    return bundle

