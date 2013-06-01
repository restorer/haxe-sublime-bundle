import json
import sublime
import os
import re
import sys
import sublime

is_st3 = int(sublime.version()) >= 3000

if is_st3:
    import Haxe.haxe.build as hxbuild
    import Haxe.haxe.panel as hxpanel
    import Haxe.haxe.hxtools as hxsrctools
    import Haxe.haxe.types as hxtypes
    import Haxe.haxe.settings as hxsettings
    import Haxe.haxe.tools.path as path_tools
    import Haxe.haxe.compiler.server as hxserver
    import Haxe.haxe.config as hxconfig
    from Haxe.haxe.execute import run_cmd
    from Haxe.haxe.log import log
    from Haxe.haxe.tools.cache import Cache

else:
    import haxe.config as hxconfig
    import haxe.build as hxbuild
    import haxe.panel as hxpanel
    import haxe.hxtools as hxsrctools
    import haxe.types as hxtypes
    import haxe.settings as hxsettings
    import haxe.tools.path as path_tools
    import haxe.compiler.server as hxserver

    from haxe.execute import run_cmd
    from haxe.log import log
    from haxe.tools.cache import Cache
is_st3 = int(sublime.version()) >= 3000

#if is_st3():
#    str = unicode

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
haxe_file_regex = "^((?:(?:[A-Za-z][:])|/)(?:[^:]*)):([0-9]+): (?:character(?:s?)|line(?:s?)|)? ([0-9]+)-?[0-9]* :(.*)$"

def haxe_build_env (project_dir):
        
    

    libPath = hxsettings.haxe_library_path()
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

    if libPath != None:
        path = os.path.normpath(os.path.join(project_dir, libPath))
        env["HAXE_LIBRARY_PATH"] = do_encode(os.sep.join(path.split("/")))
        env["HAXE_STD_PATH"] = do_encode(os.sep.join(path.split("/")))
    
    

    if haxe_inst_path != None:
        path = os.path.normpath(os.path.join(project_dir, haxe_inst_path))
        env["HAXEPATH"] = do_encode(os.sep.join(path.split("/")))
        paths.append(do_encode(os.sep.join(path.split("/"))))

    if neko_inst_path != None:
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
        self.current_build = None
        self.selecting_build = False
        self.builds = []
        self.win_id = win_id
        
        self.server = hxserver.Server(server_port)

        
        self.project_file = file

        

        self.project_id = id
        if (self.project_file != None):
            self.project_path = os.path.normpath(os.path.dirname(self.project_file))
        else:
            self.project_path = None

        self.update_compiler_info()

    def project_dir (self, default):
        p = default
        if self.project_path != None:
            p = self.project_path
        return p

    def nme_exec (self, view = None):
        return ["nme"]

    def nme_display_exec (self, view = None):
        return ["nme", "display"]

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
        
        env = haxe_build_env(self.project_dir("."))
        
        self.server.start(haxe_exec, cwd, env)
        

    def update_compiler_info (self):
        classes, packs, ver, std_paths = collect_compiler_info(self.project_path)

        #assume it's supported if no version available
        if ver is None:
            self.serverMode = True
        else:
            self.serverMode = int(ver.group(1)) >= 209
        print(ver)
        self.std_paths = std_paths
        self.std_packages = packs
        self.std_classes = ["Void","String", "Float", "Int", "UInt", "Bool", "Dynamic", "Iterator", "Iterable", "ArrayAccess"]
        self.std_classes.extend(classes)

    def is_server_mode (self):
        return self.serverMode and hxsettings.get_bool('haxe-use-server-mode', True)

    def generate_build(self, view) :

        fn = view.file_name()

        if self.current_build is not None and fn == self.current_build.hxml and view.size() == 0 :  
            e = view.begin_edit()
            hxml_src = self.current_build.make_hxml()
            view.insert(e,0,hxml_src)
            view.end_edit(e)

    def select_build( self, view ) :
        scopes = view.scope_name(view.sel()[0].end()).split()
        
        if 'source.hxml' in scopes:
            view.run_command("save")

        self.extract_build_args( view , True )


    def extract_build_args( self, view = None , force_panel = False ) :
    
        self.builds = []

        if view is None:
            view = sublime.active_window().active_view()

        fn = view.file_name()

        if fn == None:
            return

        settings = view.settings()

        #log("filename: " + fn)
        
        folder = os.path.dirname(fn)
        win = view.window()
        if win is None:
            win = sublime.active_window()
        

        folders = win.folders()
       

        
        for f in folders:
            self.builds.extend(hxbuild.find_hxml_projects(f))
            self.builds.extend(hxbuild.find_nme_projects(f))
            
        
        log( "num builds:" + str(len(self.builds)))
        

        # settings.set("haxe-complete-folder", folder)
        

        if len(self.builds) == 1:
            if force_panel : 
                sublime.status_message("There is only one build")

            # will open the build file
            #if force_panel :
            #   b = builds[0]
            #   f = b.hxml
            #   v = view.window().open_file(f,sublime.TRANSIENT) 

            self.set_current_build( view , int(0), force_panel )

        elif len(self.builds) == 0  and force_panel :
            sublime.status_message("No hxml or nmml file found")

            f = os.path.join(folder,"build.hxml")

            self.current_build = None
            self.get_build(view)
            self.current_build.hxml = f

            #for whatever reason generate_build doesn't work without transient
            win.open_file(f,sublime.TRANSIENT)

            self.set_current_build( view , int(0), force_panel )

        elif len(self.builds) > 1 and force_panel :
            buildsView = []
            log("do show panel")
            
            for b in self.builds :
                #for a in b.args :
                #   v.append( " ".join(a) )
                                
                buildsView.append( [b.to_string(), os.path.basename(b.build_file) ] )



            self.selecting_build = True
            sublime.status_message("Please select your build")

            def on_selected (i):
                #selected = i
                #selected_build = candidates[selected]
                self.set_current_build(view, i, force_panel)   

            win.show_quick_panel( buildsView , on_selected  , sublime.MONOSPACE_FONT )

        elif settings.has("haxe-build-id"):
            self.set_current_build( view , int(settings.get("haxe-build-id")), force_panel )
        
        else:
            self.set_current_build( view , int(0), force_panel )

    def set_current_build( self, view , id , force_panel ) :
        
        log( "set_current_build")
        if id < 0 or id >= len(self.builds) :
            id = 0
        
        view.settings().set( "haxe-build-id" , id ) 

        if len(self.builds) > 0 :
            self.current_build = self.builds[id]
            #log( "set_current_build - 2")
            hxpanel.default_panel().writeln( "building " + self.current_build.to_string() )
        else:
            hxpanel.default_panel().writeln( "No build found/selected" )
            
        self.selecting_build = False

        # if force_panel and self.current_build is not None: # choose NME target
        #     if self.current_build.nmml is not None:
        #         sublime.status_message("Please select a NME target")
        #         nme_targets = []
        #         for t in hxbuild.HaxeBuild.nme_targets :
        #             nme_targets.append( t[0] )

        #         view.window().show_quick_panel(nme_targets, lambda i : select_nme_target(self.current_build, i, view))

    def has_build (self):
        return self.current_build != None

    def run_build( self, view ) :
        
        if view is None: 
            view = sublime.active_window().active_view()



        


        
        if (self.has_build()):
            build = self.get_build(view)
        else:
            self.extract_build_args(view)
            build = self.get_build(view)

        if build.is_nme():
            run_exec = self.nme_exec(view)
        else:
            run_exec = self.haxe_exec(view)

        def cb (out, err):
            if (err != None and err != ""):
                msg = "build finished with errors"
                cmd = " ".join(build.get_command_args(run_exec))
                hxpanel.default_panel().writeln( "cmd: " + cmd)
                hxpanel.default_panel().writeln( msg)
                view.set_status( "haxe-status" , msg )
                hxpanel.default_panel().writeln(err)
                
            else:
                msg = "build finished successfull"
                view.set_status( "haxe-status" , msg )
                hxpanel.default_panel().writeln( msg )

            if (out != None):
                hxpanel.default_panel().writeln("---output----")
                hxpanel.default_panel().writeln( out )
                hxpanel.default_panel().writeln("-------------")    
        
        build.run(self, view, True, cb)
        
        


        
    def run_sublime_build( self, view ) :
        

        if view is None: 
            view = sublime.active_window().active_view()

        win = view.window()

        if win is None:
            win = sublime.active_window()

        log("start sublime build")


        #haxe_exec = self.haxe_exec(view)
        env = haxe_build_env(self.project_dir("."))
        
        if (self.has_build()):
            build = self.get_build(view)
        else:
            self.extract_build_args(view)
            build = self.get_build(view)

        cmd, build_folder = build.prepare_sublime_build_cmd(self, self.serverMode, view)
        
        
        
        win.run_command("haxe_exec", {
            "cmd": cmd,
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


    def get_build( self, view ) :
        
        if self.current_build is None and view.score_selector(0,"source.haxe.2") > 0 :

            fn = view.file_name()

            src_dir = os.path.dirname( fn )

            src = view.substr(sublime.Region(0, view.size()))
        
            build = hxbuild.HaxeBuild()
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
            cl = cl.encode('ascii','ignore')
            cl = cl[0:cl.rfind(".")]

            main = pack[0:]
            main.append( cl )
            build.main = ".".join( main )

            build.output = os.path.join(folder,build.main.lower() + ".js")

            log( "add cp: " + src_dir)

            build.args.append( ("-cp" , src_dir) )
            #build.args.append( ("-main" , build.main ) )

            build.args.append( ("-js" , build.output ) )
            #build.args.append( ("--no-output" , "-v" ) )

            build.hxml = os.path.join( src_dir , "build.hxml")
            
            #build.hxml = os.path.join( src_dir , "build.hxml")
            self.current_build = build
            
        return self.current_build.copy()  



# last time the sublime session file was updated
_last_modification_time = None
# used for caching the path of current project file
_last_project = None
# hash to store all active projects, files without project file use the "global" context




def run_nme( view, build ) :

    cmd = [ hxsettings.haxelib_exec(), "run", "nme", hxbuild.HaxeBuild.nme_target[2], os.path.basename(build.nmml) ]
    target = hxbuild.HaxeBuild.nme_target[1].split(" ")
    cmd.extend(target)
    cmd.append("-debug")

    view.window().run_command("haxe_exec", {
        "cmd": cmd,
        "working_dir": os.path.dirname(build.nmml),
        "file_regex": "^([^:]*):([0-9]+): (?:characters|lines): [0-9]+-([0-9]+) :.*$"
    })
    return ("" , [], "" )



def get_compiler_info_env (project_path):
    return haxe_build_env(project_path)


def collect_compiler_info (project_path):
    log("collect compiler info")
    haxe_exec = hxsettings.haxe_exec()
    
    env = get_compiler_info_env(project_path)

    if haxe_exec != "haxe":
        if project_path != None:
            haxe_exec = path_tools.join_norm(project_path, haxe_exec)
    
    
    log("cmd" + " ".join([haxe_exec, "-main", "Nothing", "-v", "--no-output"]))
    out, err = run_cmd( [haxe_exec, "-main", "Nothing", "-v", "--no-output"], env=env )
    log( out )
    log( err )
    m = classpath_line.match(out)
    
    classes = []
    packs = []
    std_paths = []

    if m is not None :
        std_paths = set(m.group(1).split(";")) - set([".","./"])
    


    for p in std_paths : 
        
        p = os.path.normpath(p)
        
        # last_pos - 2 on windows (why -2) ????? 
        # TODO check this, seems to work, but dirty
        last_pos = len(p)-2
        
        if (len(p) > 0 and (p[last_pos] == "/" or  p[last_pos] == "\\" or p[last_pos] == os.path.sep)):
            p = p[0:last_pos]
        log("path: " + p)
        log(os.path.exists(p))
        log(os.path.isdir(p))

        if len(p) > 1 and os.path.exists(p) and os.path.isdir(p):
            log("do extract")
            classes, packs = hxtypes.extract_types( p, [], [], 0, [], False )
            

    ver = re.search( haxe_version , out )
    log("collected classes: " + str(len(classes)))
    return (classes, packs, ver, std_paths)

def _get_project_file(win_id = None):
    if is_st3:
        #if win_id == None:
        #    win_id = sublime.active_window().id()
        return sublime.active_window().project_file_name()
    else:
        global _last_project
        global _last_modification_time

        log( "try getting project file")

        if win_id == None:
            win_id = sublime.active_window().id()

        project = None
        reg_session = os.path.normpath(os.path.join(sublime.packages_path(), "..", "Settings", "Session.sublime_session"))
        auto_save = os.path.normpath(os.path.join(sublime.packages_path(), "..", "Settings", "Auto Save Session.sublime_session"))
        session = auto_save if os.path.exists(auto_save) else reg_session

        print(auto_save)
        print(reg_session)
        print(session)

        if not os.path.exists(session) or win_id == None:
            return project


        mtime = os.path.getmtime(session)

        if (_last_modification_time is not None 
            and mtime == _last_modification_time
            and _last_project != None):
            _last_modification_time = mtime
            log( "cached project id")
            return _last_project
        else:
            _last_modification_time = mtime
        try:
            with open(session, 'r') as f:
                # Tabs in strings messes things up for some reason
                j = json.JSONDecoder(strict=False).decode(f.read())
                for w in j['windows']:
                    if w['window_id'] == win_id:
                        if "workspace_name" in w:
                            if sublime.platform() == "windows":
                                # Account for windows specific formatting
                                project = os.path.normpath(w["workspace_name"].lstrip("/").replace("/", ":/", 1))
                            else:
                                project = w["workspace_name"]
                            break
        except:
            pass

        # Throw out empty project names
        if project == None or re.match(".*\\.sublime-project", project) == None or not os.path.exists(project):
            project = None

        _last_project = project
        return project


def select_nme_target( build, i, view ):
    target = hxbuild.HaxeBuild.nme_targets[i]
    if build.nmml is not None:
        hxbuild.HaxeBuild.nme_target = target
        view.set_status( "haxe-build" , build.to_string() )
        hxpanel.default_panel().status( "haxe-build" , build.to_string() )


_projects = Cache()

import sublime
from os.path import expanduser
user_home = expanduser("~")
log_file = os.path.join(user_home, str("st3_haxe_log.txt"))

def destroy ():
    
    file_log("destroy called")

    global _projects
    file_log("keys " + str(list(_projects.data.keys())))
    for p in _projects.data.keys():
        
        project = _projects.data[p][1]
        file_log("project " + project.project_file)
        project.destroy()
    _projects = Cache()



def file_log (msg):
    f = open(log_file , "a+" )
    f.write( str(msg) + str("\n") )
    f.close()

def plugin_unloaded_handler():
    pass
    #destroy()
    


def plugin_unloaded():
    plugin_unloaded_handler()

def unload_handler():
    plugin_unloaded_handler()



_next_server_port = [6000]
def current_project(view = None):


    win_ids = [w.id() for w in sublime.windows()]

    remove = []
    for p in _projects.data.keys():
        proj = _projects.get_or_default(p, None)
        if proj != None and proj.win_id not in win_ids:
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


    

    file = _get_project_file()
    
    if (view != None):
        win = view.window();
        if win == None:
            win = sublime.active_window()
    else:
        win = sublime.active_window()
    if (file == None):
        id = "global" + str(win.id())
    else:
        id = file
    log("project id:" + id)
    log("project file:" + str(file))
    log("win.id:" + str(win.id()))

    def create ():
        p = Project(id, file, win.id(), _next_server_port[0])
        _next_server_port[0] = _next_server_port[0] + 20
        return p
    res = _projects.get_or_insert(id, create )
    
    return res
