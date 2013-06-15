import sublime
import sublime_plugin

from haxe.tools import viewtools
from haxe import project as hxproject
from haxe.tools import scopetools

from haxe import config as hxconfig

from haxe.log import log

from haxe.completion import hx
from haxe.completion import hxml
from haxe.completion import hxsl

import time


class CompletionListener( sublime_plugin.EventListener ):

    def on_query_completions(self, view, prefix, locations):
        project = hxproject.current_project(view)
        return dispatch_auto_complete(project, view, prefix, locations[0])

# auto complete is triggered, this function dispatches to actual completion based
# on the file type of the current view

def get_completion_scopes (view, location):
    return viewtools.get_scopes_at(view, location)

def get_completion_offset (location, prefix):
    return location - len(prefix)

def can_run_completion(offset, scopes):
    return False if offset == 0 else is_supported_scope(scopes)

def is_supported_scope(scopes):
    return not scopetools.contains_string_or_comment(scopes)    

def empty_handler(project, view, offset, prefix):
    return []

def get_auto_complete_handler (view, scopes):
    
    handler = None

    if hxconfig.SOURCE_HXML in scopes: # hxml completion
        handler = hxml.auto_complete
    elif hxconfig.SOURCE_HAXE in scopes : # hx can be hxsl or haxe
        if viewtools.is_hxsl(view) :
            handler = hxsl.auto_complete # hxsl completion
        else :
            handler = hx.auto_complete # hx completion
    else: # empy handler
        handler = empty_handler
            
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


