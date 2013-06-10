
import sublime
import sublime_plugin

is_st3 = int(sublime.version()) >= 3000

if is_st3:
    import Haxe.haxe.tools.view as view_tools
    import Haxe.haxe.project as hxproject
    import Haxe.haxe.tools.scope as scope_tools
    import Haxe.haxe.config as hxconfig

    from Haxe.haxe.log import log

    import Haxe.haxe.completion.hx.base as hx 
    import Haxe.haxe.completion.hxml.base as hxml
    import Haxe.haxe.completion.hxsl.base as hxsl
else:
    import haxe.tools.view as view_tools
    import haxe.project as hxproject
    import haxe.tools.scope as scope_tools
    import haxe.config as hxconfig

    from haxe.log import log

    import haxe.completion.hx.base as hx 
    import haxe.completion.hxml.base as hxml
    import haxe.completion.hxsl.base as hxsl


import time




class CompletionListener( sublime_plugin.EventListener ):

    def on_query_completions(self, view, prefix, locations):
        project = hxproject.current_project(view)
        return dispatch_auto_complete(project, view, prefix, locations[0])

# auto complete is triggered, this function dispatches to actual completion based
# on the file type of the current view

def get_completion_scopes (view, location):
    return view_tools.get_scopes_at(view, location)

def get_completion_offset (location, prefix):
    return location - len(prefix)

def can_run_completion(offset, scopes):
    return False if offset == 0 else is_supported_scope(scopes)

def is_supported_scope(scopes):
    return not scope_tools.contains_string_or_comment(scopes)    

def get_auto_complete_handler (view, scopes):
    
    handler = None

    if hxconfig.SOURCE_HXML in scopes: # hxml completion
        handler = hxml.auto_complete
    elif hxconfig.SOURCE_HAXE in scopes : # hx can be hxsl or haxe
        if view_tools.is_hxsl(view) :
            handler = hxsl.auto_complete # hxsl completion
        else :
            handler = hx.auto_complete # hx completion
    else: # empy handler
        handler = lambda project, view, offset: []
            
    return handler

def dispatch_auto_complete (project, view, prefix, location):
    start_time = time.time()

    offset = get_completion_offset(location, prefix)

    scopes = get_completion_scopes(view, location)

    comps = None

    if can_run_completion(offset, scopes):
        handler = get_auto_complete_handler(view, scopes);
        comps = handler(project, view, offset, prefix)
    else:
        comps = []

    log_completion_info(start_time, time.time(), comps)

    return comps



def log_completion_info (start_time, end_time, comps):
    run_time = end_time-start_time
    log("on_query_completion time: " + str(run_time))
    log("number of completions: " + str(len(comps)))


