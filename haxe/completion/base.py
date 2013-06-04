
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




class HaxeCompleteListener( sublime_plugin.EventListener ):

    def __del__( self ) :
        hxproject.destroy()

    def on_load( self, view ) :

        if view is not None and view.file_name() is not None and view_tools.is_supported(view): 
            def on_load_delay():
                if not hxproject.current_project(view).has_build():
                    hxproject.current_project(view).generate_build( view )

            sublime.set_timeout(lambda: on_load_delay, 100)


    def on_post_save( self , view ) :
        if view is not None and view.file_name() is not None and view_tools.is_hxml(view):
            project = hxproject.current_project(view)
            project.clear_build()
            
    # if view is None it's a preview
    def on_activated( self , view ) :
        log("on_activated")
        if view is not None and view.file_name() is not None and view_tools.is_supported(view): 

            sublime.set_timeout(lambda: hxproject.current_project(view), 100)
            
            #if (project.)
            #build = project.get_build(view)
            #project.extract_build_args( view )
            #project.generate_build(view)    

    def on_pre_save( self , view ) :
        if view_tools.is_haxe(view) :
            view_tools.create_missing_folders(view)

    # prefix describes the searchstring for autocompletion
    # e.g. this.ff| has the prefix ff
    # e.g. this.| has an empty string as prefix
    # locations describes the cursor positions (multiple cursor)
    # but only the first one is handled for completion
    def on_query_completions(self, view, prefix, locations):
        log("HERE: on_query_completions triggered")

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
        comps = handler(project, view, offset)
    else:
        comps = []

    log_completion_info(start_time, time.time(), comps)

    return comps



def log_completion_info (start_time, end_time, comps):
    run_time = end_time-start_time
    log("on_query_completion time: " + str(run_time))
    log("number of completions: " + str(len(comps)))


