import json
import sublime
import sublime_plugin
import os
import re
import sys

from haxe.plugin import is_st3, is_st2

import haxe.build as hxbuild
import haxe.panel as hxpanel
import haxe.hxtools as hxsrctools
import haxe.types as hxtypes
import haxe.settings as hxsettings
import haxe.execute as hxexecute
import haxe.tools.path as pathtools
import haxe.tools.view as viewtools
import haxe.tools.sublimetools as sublimetools
import haxe.lib as hxlib
import haxe.compiler.server as hxserver

import haxe.config as hxconfig
from haxe.log import log
from haxe.tools.cache import Cache

# TODO split this module into smaller chunks


class ProjectListener( sublime_plugin.EventListener ):

    def on_post_save( self , view ) :
        if view is not None and view.file_name() is not None and viewtools.is_hxml(view):
            project = current_project(view)
            project.clear_build()
            
    # if view is None it's a preview
    def on_activated( self , view ) :
        log("on_activated")
        if view is not None and view.file_name() is not None and viewtools.is_supported(view): 
            def on_load_delay():
                current_project(view).generate_build( view )

            sublime.set_timeout(on_load_delay, 100)
            

    def on_pre_save( self , view ) :
        if viewtools.is_haxe(view) :
            viewtools.create_missing_folders(view)

class ProjectCompletionContext:

    def __init__(self):
        
        self.running = Cache()
        self.trigger = Cache(1000)
        self.current_id = None   
        self.errors = []
        self.async = Cache(1000)
        self.current = {
            "input" : None,
            "output" : None
        }

    def add_completion_result (self, comp_result):
        self.async.insert(comp_result.ctx.view_id, comp_result)

    def is_equivalent_completion_already_running(self, ctx):
        # check if another completion with the same properties is already running
        # in this case we don't need to start a new completion
        complete_offset = ctx.complete_offset
        view_id = ctx.view_id

        last_completion_id = self.current_id
        running_completion = self.running.get_or_default(last_completion_id, None)    
        return running_completion is not None and running_completion[0] == complete_offset and running_completion[1] == view_id

    def run_if_still_up_to_date (self, comp_id, run):
        self.running.delete(comp_id)
        if self.current_id == comp_id:
            run()
        
        

    def set_new_completion (self, ctx):
        # store current completion id and properties
        self.running.insert(ctx.id, (ctx.complete_offset, ctx.view_id))
        self.current_id = ctx.id

        self.set_errors([])

    def set_trigger(self, view, options):
        log("SET TRIGGER")
        self.trigger.insert(view.id(), options)

    def clear_completion (self):
        self.current = {
            "input" : None,
            "output" : None
        }

    def set_errors (self, errors):
        self.errors = errors

    def get_and_delete_trigger(self, view):
        return self.trigger.get_and_delete(view.id(), None)

    def get_and_delete_async(self, view):
        return self.async.get_and_delete(view.id(), None)

    def get_async(self, view):
        return self.async.get_or_default(view.id(), )

    def delete_async(self, view):
        return self.async.delete(view.id())


classpath_line = re.compile("Classpath : (.*)")

haxe_version = re.compile("haxe_([0-9]{3})",re.M)

# allow windows drives
win_start = "(?:(?:[A-Za-z][:])"
unix_start = "(?:[/]?)" 
haxe_file_regex = "^(" + win_start + "|" + unix_start + ")?(?:[^:]*)):([0-9]+): (?:character(?:s?)|line(?:s?))? ([0-9]+)-?[0-9]*\s?:(.*)$"

def haxe_build_env (project_dir):
        
    lib_path = hxsettings.haxe_library_path()
    haxe_inst_path = hxsettings.haxe_inst_path()
    neko_inst_path = hxsettings.neko_inst_path()

    envPath = os.environ.copy()["PATH"]
    
    env = {}

    paths = list()

    def do_encode(s):
        if is_st3:
            return s
        else:
            return s.encode(sys.getfilesystemencoding())

    if lib_path is not None:
        path = os.path.normpath(os.path.join(project_dir, lib_path))
        env["HAXE_LIBRARY_PATH"] = do_encode(os.sep.join(path.split("/")))
        env["HAXE_STD_PATH"] = do_encode(os.sep.join(path.split("/")))
    

    if haxe_inst_path is not None:
        path = os.path.normpath(os.path.join(project_dir, haxe_inst_path))
        env["HAXEPATH"] = do_encode(os.sep.join(path.split("/")))
        paths.append(do_encode(os.sep.join(path.split("/"))))

    if neko_inst_path is not None:
        path = os.path.normpath(os.path.join(project_dir, neko_inst_path))
        env["NEKO_INSTPATH"] = do_encode(os.sep.join(path.split("/")))
        paths.append(do_encode(os.sep.join(path.split("/"))))

    
    if len(paths) > 0:
        env["PATH"] = os.pathsep.join(paths) + os.pathsep + envPath

    
    print(str(env))
    return env

class Project:
    def __init__(self, id, file, win_id, server_port):
        self.completion_context = ProjectCompletionContext()
        self._haxelib_manager = hxlib.HaxeLibManager(self)
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

        self.update_compiler_info()

    @property
    def haxelib_manager (self):
        return self._haxelib_manager

    def project_dir (self, default):
        return self.project_path if self.project_path is not None else default
            

    def nme_exec (self, view = None):
        return ["nme"]

    def openfl_exec (self, view = None):
        return ["openfl"]

    def haxelib_exec (self, view = None):
        return [hxsettings.haxelib_exec()]

    def haxe_exec (self, view = None):
        haxe_exec = hxsettings.haxe_exec(view)
        if (haxe_exec != "haxe"):
            cwd = self.project_dir(".")
            haxe_exec = os.path.normpath(os.sep.join(os.path.join(cwd, hxsettings.haxe_exec(view)).split("/")))
        return [haxe_exec]

    
    def haxe_env (self, view = None):
        return haxe_build_env(self.project_dir("."))
    
    
    def start_server(self, view):
        cwd = self.project_dir(".")
        haxe_exec = self.haxe_exec(view)[0]
        
        env = self.haxe_env()
        
        self.server.start(haxe_exec, cwd, env)
        

    def update_compiler_info (self):
        classes, packs, ver, std_paths = collect_compiler_info(self.haxe_exec(), self.project_path)

        #assume it's supported if no version available
        self.server_mode = ver is None or ver >= 209
        
        self.std_paths = std_paths
        self.std_packages = packs
        self.std_classes = ["Void","String", "Float", "Int", "UInt", "Bool", "Dynamic", "Iterator", "Iterable", "ArrayAccess"]
        self.std_classes.extend(classes)

    def is_server_mode (self):
        return self.server_mode and hxsettings.use_haxe_servermode()


    def generate_build(self, view):
        fn = view.file_name()
        log("generate build")
        if self.current_build is not None and isinstance(self.current_build, hxbuild.HxmlBuild) and fn == self.current_build.hxml and view.size() == 0 :
            log("do edit")
            def run_edit(v, e):
                hxml_src = self.current_build.make_hxml()
                log("hxml_src")
                v.insert(e,0,hxml_src)
                v.end_edit(e)

            viewtools.async_edit(view, run_edit)

    def select_build( self, view ) :
        scopes = view.scope_name(view.sel()[0].end()).split()
        
        if 'source.hxml' in scopes:
            view.run_command("save")

        self.extract_build_args( view , True )


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


    def extract_build_args( self, view = None , force_panel = False ) :

        folders = self._get_folders(view)
        
        self.builds = self._find_builds_in_folders(folders)
        
        num_builds = len(self.builds)

        if num_builds == 1:
            if force_panel : 
                sublime.status_message("There is only one build")
            self.set_current_build( view , int(0) )
        elif num_builds == 0 and force_panel :
            sublime.status_message("No build files found (e.g. hxml, nmml, xml)")
            self.create_new_hxml(view, folders[0])
        elif num_builds > 1 and force_panel :
            self.show_build_selection_panel(view)
        else:
            self.set_current_build( view , int(0) )


    def create_new_hxml (self, view, folder):
        win = sublime.active_window()
        f = os.path.join(folder,"build.hxml")

        self.current_build = None
        self.get_build(view)
        self.current_build.hxml = f

        #for whatever reason generate_build doesn't work without transient
        win.open_file(f,sublime.TRANSIENT)

        self.set_current_build( view , int(0) )

    def show_build_selection_panel(self, view):
        
        buildsView = [[b.to_string(), os.path.basename(b.build_file) ] for b in self.builds]

        self.selecting_build = True
        sublime.status_message("Please select your build")

        def on_selected (i):
            self.selecting_build = False
            self.set_current_build(view, i)   

        win = sublime.active_window()
        win.show_quick_panel( buildsView , on_selected  , sublime.MONOSPACE_FONT )        

    def set_current_build( self, view , id ) :
        
        log( "set_current_build")
        
        if id < 0 or id >= len(self.builds) :
            id = 0
        
        if len(self.builds) > 0 :
            self.current_build = self.builds[id]
            self.current_build.set_std_classes(list(self.std_classes))
            self.current_build.set_std_packs(list(self.std_packages))
            hxpanel.default_panel().writeln( "build selected: " + self.current_build.to_string() )
        else:
            hxpanel.default_panel().writeln( "No build found/selected" )
            
    def has_build (self):
        return self.current_build is not None

    def check_build(self, view):
        self._build(view, "check")

    def just_build(self, view):
        self._build(view, "build")
        
    def run_build( self, view ) :
        self._build(view, "run")
    
    def _build(self, view, type = "run"):

        if view is None: 
            view = sublime.active_window().active_view()

        win = view.window()

        env = haxe_build_env(self.project_dir("."))
        
        if self.has_build():
            build = self.get_build(view)
        else:
            self.extract_build_args(view)
            build = self.get_build(view)

        if type == "run": # build and run
            cmd, build_folder = build.prepare_run_cmd(self, self.server_mode, view)
        elif type == "build": # just build
            cmd, build_folder = build.prepare_build_cmd(self, self.server_mode, view)
        else: # only check for errors
            cmd, build_folder = build.prepare_check_cmd(self, self.server_mode, view)
        
        
        hxpanel.default_panel().writeln("running: " + " ".join(cmd))

        
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
        
        file_log("destroy server")
        self.server.stop()



    # TODO rewrite this function and make it understandable
    def create_default_build (self, view):
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


    def get_build( self, view ) :
        
        if self.current_build is None and view.score_selector(0,"source.haxe.2") > 0 :
            self.current_build = self.create_default_build(view)
           
        return self.current_build.copy()  



def get_compiler_info_env (project_path):
    return haxe_build_env(project_path)





def collect_compiler_info (haxe_exec, project_path):
    env = get_compiler_info_env(project_path)

    cmd = haxe_exec
    cmd.extend(["-main", "Nothing", "-v", "--no-output"])

    out, err = hxexecute.run_cmd( cmd, env=env )

    std_classpaths = extract_std_classpaths(out)
    
    classes,packs = collect_std_classes_and_packs(std_classpaths)
            
    ver = extract_haxe_version(out)
    
    return (classes, packs, ver, std_classpaths)

def extract_haxe_version (out):
    ver = re.search( haxe_version , out )
    return int(ver.group(1)) if ver is not None else None


def remove_trailing_path_sep(path):
    if len(path) > 1:
        last_pos = len(path)-1
        last_char = path[last_pos]
        if last_char == "/" or  last_char == "\\" or last_char == os.path.sep:
            path = path[0:last_pos]
    return path

def is_valid_classpath(path):
    return len(path) > 1 and os.path.exists(path) and os.path.isdir(path)

def extract_std_classpaths (out):
    m = classpath_line.match(out)
        
    std_classpaths = []

    all_paths = m.group(1).split(";")
    ignored_paths = [".","./"]

    std_paths = set(all_paths) - set(ignored_paths) if m is not None else []
    
    for p in std_paths : 
        p = os.path.normpath(p)
        
        p = remove_trailing_path_sep(p)

        if is_valid_classpath(p):
            std_classpaths.append(p)

    return std_classpaths


def collect_std_classes_and_packs(std_cps):
    classes = []
    packs = []
    for p in std_cps : 
        classes_p, packs_p = hxtypes.extract_types( p, [], [], 0, [], False )
        classes.extend(classes_p)
        packs.extend(packs_p)

    return classes, packs


_projects = Cache()

import sublime
from os.path import expanduser
user_home = expanduser("~")
log_file = os.path.join(user_home, str("st3_haxe_log.txt"))



def file_log (msg):
    f = open(log_file , "a+" )
    f.write( str(msg) + str("\n") )
    f.close()


#def destroy ():
#    
#    file_log("destroy called")
#
#    global _projects
#    file_log("keys " + str(list(_projects.data.keys())))
#    for p in _projects.data.keys():
#        
#        project = _projects.data[p][1]
#        file_log("project " + project.project_file)
#        project.destroy()
#    _projects = Cache()



#def plugin_unloaded_handler():
#    pass
#    #destroy()
#    
#
#
#def plugin_unloaded():
#    plugin_unloaded_handler()
#
#def unload_handler():
#    plugin_unloaded_handler()



_next_server_port = 6000

def cleanup_projects():
    win_ids = [w.id() for w in sublime.windows()]
    remove = []
    for p in _projects.data.keys():
        proj = _projects.get_or_default(p, None)
        if proj is not None and proj.win_id not in win_ids:
            remove.append(p)
            # project should be closed
    
    log(remove)
    for pid in remove:
        log(pid)
        project = _projects.data[pid][1]
        project.destroy()
        log("delete project from memory")
        del _projects.data[pid]
        del project


def get_project_id(file, win):
    if (file == None):
        id = "global" + str(win.id())
    else:
        id = file

    return id

def get_window (view):
    if (view is not None):
        win = view.window();
        if win == None:
            win = sublime.active_window()
    else:
        win = sublime.active_window()
    return win

def current_project(view = None):


    cleanup_projects()

    file = sublimetools.get_project_file()
    
    win = get_window(view)
    
    id = get_project_id(file, win)

    log("project id:" + id)
    log("project file:" + str(file))
    log("win.id:" + str(win.id()))

    res = _projects.get_or_insert(id, lambda:create_project(id, file, win) )
    
    return res

def create_project (id, file, win):
    global _next_server_port
    p = Project(id, file, win.id(), _next_server_port)
    _next_server_port = _next_server_port + 20
    return p