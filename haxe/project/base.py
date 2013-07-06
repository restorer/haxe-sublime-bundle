import sublime
import sublime_plugin
import os

from haxe.tools import viewtools
from haxe.tools import sublimetools

from os.path import expanduser
from haxe.log import log

from haxe.tools.cache import Cache

from haxe.project.tools import get_window
from haxe.project.project import Project

from haxe.tools.stringtools import encode_utf8


_projects = Cache()
_user_home = expanduser("~")
_log_file = os.path.join(_user_home, str("st3_haxe_log.txt"))
_next_server_port = 6000

def file_log (msg):
    f = open(_log_file , "a+" )
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
    #log("project file:" + encode_utf8(file))
    log("win.id:" + str(win.id()))

    res = _projects.get_or_insert(id, lambda:create_project(id, file, win) )
    
    return res

def create_project (id, file, win):
    global _next_server_port
    
    p = Project(id, file, win.id(), _next_server_port)
    _next_server_port = _next_server_port + 20
    return p

class ProjectListener( sublime_plugin.EventListener ):

    def on_post_save( self , view ) :
        if view is not None and view.file_name() is not None and viewtools.is_hxml(view):
            project = current_project(view)
            project.clear_build()
            
    # if view is None it's a preview
    def on_activated( self , view ) :
        
        if view is not None and view.file_name() is not None and viewtools.is_supported(view): 
            def on_load_delay():
                current_project(view).generate_build( view )

            sublime.set_timeout(on_load_delay, 100)
            

    def on_pre_save( self , view ) :
        if viewtools.is_haxe(view) :
            viewtools.create_missing_folders(view)



