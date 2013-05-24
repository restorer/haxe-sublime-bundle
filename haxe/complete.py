import sublime, sublime_plugin
import time
import os
import re

import haxe.settings as hxsettings
import haxe.lib as hxlib
import haxe.panel as hxpanel
import haxe.config as hxconfig
import haxe.types as hxtypes
import haxe.project as hxproject
import haxe.hxtools as hxsrctools
import haxe.tools.view as view_tools
import haxe.tools.scope as scope_tools
import haxe.temp as hxtemp


from haxe.compiler.output import get_completion_output
from haxe.log import log



print "initialize complete.py"

lib_flag = re.compile("-lib\s+(.*?)")

control_struct = re.compile( "\s+(if|switch|for|while)\s*\($" );

bundle_file = __file__
bundle_path = os.path.abspath(bundle_file)
bundle_dir = os.path.dirname(bundle_path)


# ------------------- HXSL COMPLETION -------------------------

def hxsl_auto_complete( project, view , offset ) :
    comps = []
    for t in ["Float","Float2","Float3","Float4","Matrix","M44","M33","M34","M43","Texture","CubeTexture","Int","Color","include"] :
        comps.append( ( t , "hxsl Type" ) )
    return comps

# ------------------- HXML COMPLETION -------------------------

def hxml_auto_complete( project, view , offset ) :
    src = view.substr(sublime.Region(0, offset))
    current_line = src[src.rfind("\n")+1:offset]
    m = lib_flag.match( current_line )
    if m is not None :
        return hxlib.HaxeLib.get_completions()
    else :
        return []


class CompletionContext:
    pass

# ------------------- HX COMPLETION -------------------------

def get_completions_from_background_run(background_result, view):
    comps1 = background_result[0]
    hints1 = background_result[1]
    comp_type = background_result[2]

    has_comps = len(comps1) > 0
    has_hints = len(hints1) > 0 

    comps = None

    if (not has_comps and not has_hints and (hxsettings.no_fuzzy_completion() or comp_type == "hint")):
        comps = cancel_completion(view)
    else:
        comps = combine_hints_and_comps(comps1, hints1, comp_type)

    return comps


def hx_auto_complete(project, view, offset):

    # if completion is triggered by a background completion process
    # completion return the result
    background_result = project.completion_context.get_and_delete_delayed(view)

    if background_result is not None:
        comps = get_completions_from_background_run(background_result, view)
    else:
        # get build and maybe use cache
        comps = get_completions_regular(project, view, offset)
    return comps

def filter_top_level_completions (offset_char, all_comps):
    log("number of top level completions all:" + str(len(all_comps)))
        
    comps = []

    is_lower = offset_char in "abcdefghijklmnopqrstuvwxyz"
    is_upper = offset_char in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    is_digit = offset_char in "0123456789"
    is_special = offset_char in "$_#"
    offset_upper = offset_char.upper()
    offset_lower = offset_char.lower()
    if is_lower or is_upper or is_digit or is_special:
        
        for c in all_comps:

            id = c[1]

            if (offset_char in id
                or (is_upper and offset_lower in id)
                or (is_lower and offset_upper in id)):
                comps.append(c)
    else:
        comps = all_comps

    log("number of top level completions filtered" + str(len(comps)))
    return comps

def combine_hints_and_comps (comps, hints, comp_type):
    def make_hint_comp (h):
        is_only_type = len(h) == 1
        res = None
        if is_only_type:
            res = (h[0] + " - No Completion", "${}")
        else:
            only_next = hxsettings.smarts_hints_only_next()

            params = h[0:len(h)-1];
            params2 = params if not only_next else h[0:1]
            show = "" + ",".join([param for param in params]) + ""
            insert = ",".join(["${" + str(index+1) + ":" + param + "}" for index, param in enumerate(params2)])
            log(insert)
            res = (show, insert)
        return res

    all_comps = [make_hint_comp(h) for h in hints]

    if comp_type != "hint":
        all_comps.extend(comps)
    return all_comps

def get_completions_regular(project, view, offset):
    if not project.has_build():
        project.extract_build_args()
    build = project.get_build( view ).copy()
    cache = project.completion_context.current
    
    return hx_normal_auto_complete(project, view, offset, build, cache)


def is_iterator_completion(src, offset):
    o = offset
    s = src
    return o > 3 and s[o] == "\n" and s[o-1] == "." and s[o-2] == "." and s[o-3] != "."



def should_trigger_manual_hint_completion(manual_completion, complete_char):
    return not manual_completion and complete_char in "(,"


def is_same_completion_already_running(project, complete_offset, view):
    last_completion_id = project.completion_context.current_id
    running_completion = project.completion_context.running.get_or_default(last_completion_id, None)    
    return running_completion is not None and running_completion[0] == complete_offset and running_completion[1] == view.id()


def should_include_top_level_completion(src, comp_type, is_new, complete_offset, offset, prev_symbol_is_comma, on_demand, in_control_struct, complete_char):
    skipped = src[complete_offset:offset]
    toplevel_complete = False if not prev_symbol_is_comma else (hxsrctools.skippable.search( skipped ) is None and hxsrctools.in_anonymous.search( skipped ) is None)
    toplevel_complete = (toplevel_complete or complete_char in ":(," or in_control_struct) and not on_demand
    return comp_type != "hint" and (is_new or toplevel_complete)


def get_toplevel_completion_if_reasonable(project, src, build, macro_completion, comp_type, is_new, offset_char, complete_offset, offset, prev_symbol_is_comma, on_demand, in_control_struct, complete_char):
    
    if should_include_top_level_completion(src, comp_type, is_new, complete_offset, offset, prev_symbol_is_comma, on_demand, in_control_struct, complete_char):
        all_comps = get_toplevel_completion( project, src , build.copy(), macro_completion, is_new )
        comps = filter_top_level_completions(offset_char, all_comps)
    else:
        log("comps_without_top_level")
        comps = []
    return comps


def get_completion_id ():
    # make the current time the id for this completion
    return time.time()

def hx_normal_auto_complete(project, view, offset, build, cache):

    log("------- COMPLETION START -----------")

    completion_id = get_completion_id()

    trigger = project.completion_context.get_and_delete_trigger(view)
    comp_type = project.completion_context.get_and_delete_trigger_comp(view)
    
    manual_completion = trigger is not hxproject.TRIGGER_SUBLIME

    macro_completion = trigger is hxproject.TRIGGER_MANUAL_MACRO
    src = view_tools.get_content(view)
    orig_file = view.file_name()
    #src_dir = os.path.dirname(orig_file)
    

    commas, complete_offset, prev_symbol_is_comma, is_new = get_completion_info(view, offset, src)
    
    complete_char = src[complete_offset-1]

    offset_char = src[offset]

    res = None
    
    # autocompletion is triggered, but its already 
    # running as a background process, starting it
    # again would result in multiple queries for
    # the same view and src position
    if is_same_completion_already_running(project, complete_offset, view):
        log("cancel completion, same is running")
        res = cancel_completion(view)
    elif should_trigger_manual_hint_completion(manual_completion, complete_char):
        trigger_manual_completion_type(view, "hint")
        res = cancel_completion(view)
    elif not manual_completion:
        trigger_manual_completion(view, macro_completion )
        res = cancel_completion(view)
    elif is_iterator_completion(src, offset):
        log("iterator completion")
        res = [(".\tint iterator", "..")]
    else:
    
        #toplevel_complete = should_include_top_level_completion(src, comp_type, is_new, complete_offset, offset, prev_symbol_is_comma, on_demand, in_control_struct, complete_char)
        
        src_until_completion_offset = src[0:complete_offset]

        in_control_struct = control_struct.search( src_until_completion_offset ) is not None

        on_demand = hxsettings.top_level_completions_on_demand()

        is_directly_after_control_struct = in_control_struct and complete_char == "("

        #comp_type != "hint" and (is_new or (toplevel_complete and (in_control_struct or complete_char not in "(,")))
        only_top_level = is_new or is_directly_after_control_struct
        #log("is_after_cs: " + str(is_directly_after_control_struct))

        if only_top_level:
            log("is_new or is_directly_after_control_struct")
            log("is_after_cs: " + str(is_directly_after_control_struct))
            log("is new: " + str(is_new))
            comps = get_toplevel_completion_if_reasonable(project, src, build.copy(), macro_completion, comp_type, is_new, offset_char, complete_offset, offset, prev_symbol_is_comma, on_demand, in_control_struct, complete_char)
            res = comps
        else:

            async = hxsettings.is_delayed_completion()
            
            

            current_input = create_completion_input_key(orig_file, complete_offset, commas, src, macro_completion, complete_char, comp_type)

            last_input = cache["input"]

            log("USE ASYNC COMPLETION: " + str(async))

            use_cache = use_completion_cache(last_input, current_input)


            comps1 = []
            status = ""
            hints = None

            comps = get_toplevel_completion_if_reasonable(project, src, build.copy(), macro_completion, comp_type, is_new, offset_char, complete_offset, offset, prev_symbol_is_comma, on_demand, in_control_struct, complete_char)  
            if use_cache :
                log("USE COMPLETION CACHE")
                ret, comps1, status, hints, comp_type = cache["output"]
            else :
                ret, comps1, status, hints = get_fresh_completions(commas, complete_offset, complete_char, build, src, orig_file, project, view, macro_completion, comp_type, comps, completion_id, async, cache, current_input)
                if not use_cache and async and hxsettings.only_delayed_completions():
                    log("delayed is running: completion cancelled")
                    return cancel_completion(view, True)

            comps.extend(comps1)

            if not async:
                cache["output"] = (ret,comps1,status, hints, comp_type)
                cache["input"] = current_input
            
            log_completion_status(status, comps, hints)            

            res = combine_hints_and_comps(comps, hints, comp_type)

    return res

def log_completion_status(status, comps, hints):
    if status != "":
        if len(comps) > 0 or len(hints) > 0:
            log(status)
        else:
            hxpanel.default_panel().writeln( status )    

def get_fresh_completions(commas, complete_offset, complete_char, build, src, orig_file, project, view, macro_completion, comp_type, comps, completion_id, delayed, cache, current_input):
    log("not use cache")

    if supported_compiler_completion_char(complete_char): 
        log(build)

        tmp_source = src[:complete_offset] + "|" + src[complete_offset:]

        temp_path, temp_file = hxtemp.create_temp_path_and_file(build, orig_file, tmp_source)

        if temp_path is None or temp_file is None:
            # this should never happen, todo proper error message
            log("completion error")
            return ("", [], "", [])

        build.add_classpath(temp_path)
        display = temp_file + "@0"
        def run_compiler_completion (cb, async):
            return get_compiler_completion( project, build, view, display, temp_file, orig_file , async, cb, macro_completion, comp_type )
        if delayed:
            log("run delayed compiler completion")

            run_async_completion(project, completion_id, list(comps), temp_file, orig_file,temp_path,
                view, cache, current_input, complete_offset, run_compiler_completion, comp_type)
            
            res = ("", [], "", [])
        else:
            log("run normal compiler completion")
            ret0 = []
            err0 = []
            def cb(out1, err1):
                ret0.append(out1)
                err0.append(err1)
            run_compiler_completion(cb, False)
            ret = ret0[0]
            err = err0[0]
            
            hxtemp.remove_path(temp_path)
            hints, comps1, status, errors = get_completion_output(temp_file, orig_file, err, commas)
            comps1 = [(t[0], t[1]) for t in comps1]
            highlight_errors( errors, view )
            res = (ret, comps1, status, hints )
    else:
        log("not supported completion char")
        res = ("",[], "", [])

    return res

def async_completion_finished(ret_, err_, temp_file, orig_file, commas, timer, project, view, temp_path, comps, completion_id, comp_type, cache, current_input, basic_comps, view_id, only_delayed, macro_completion, show_delay):
    hints, comps_, status_, errors = get_completion_output(temp_file, orig_file, err_, commas)

        
    comps_ = [(t[0], t[1]) for t in comps_]
            
    log("background completion time: " + str(time.time() - timer))
    project.completion_context.set_errors(errors)
    highlight_errors( errors, view )

    
    hxtemp.remove_path(temp_path)
    comps.extend(comps_)

    
    if completion_id == project.completion_context.current_id:
        cache["output"] = (ret_,comps_,status_, hints, comp_type)
        cache["input"] = current_input
    else:
        log("ignored completion")
    
    # do we still need this completion, or is it old
    has_new_comps = len(comps) > len(basic_comps)
    has_hints = len(hints) > 0
    if completion_id == project.completion_context.current_id and (has_new_comps or hxsettings.only_delayed_completions() or has_hints):
        
        project.completion_context.delayed.insert(view_id, (comps, hints, comp_type))
        if only_delayed:
            log("trigger_auto_complete")
            if (comp_type == "hint"):
                trigger_manual_completion_type(view,comp_type)    
            else:
                trigger_manual_completion(view,macro_completion)
            #view.run_command('auto_complete', {'disable_auto_insert': True})
        else:
            view.run_command('hide_auto_complete')
            sublime.set_timeout(lambda : trigger_manual_completion(view,macro_completion), show_delay)
            #sublime.set_timeout(lambda : view.run_command('auto_complete', {'disable_auto_insert': True}), show_delay)
    else:
        log("ignore background completion")
    
    project.completion_context.running.delete(completion_id)


def run_async_completion(project, completion_id, basic_comps, temp_file, orig_file, temp_path, 
        view, cache, current_input, complete_offset, run_compiler_completion, comp_type):
    hide_delay, show_delay = hxsettings.get_completion_delays()

    commas = current_input[2]
    macro_completion = current_input[4]
    
    view_id = view.id()
    
    comps = list(basic_comps) # make copy

    only_async = hxsettings.only_delayed_completions()

    timer = time.time()

    def in_main (ret_, err_):
        async_completion_finished(ret_, err_, temp_file, orig_file, commas, timer, project, view, temp_path, comps, completion_id, comp_type, cache, current_input, basic_comps, view_id, only_async, macro_completion, show_delay)
        
    def on_result(ret_, err_):
        # replace current completion workaround
        # delays are customizable with project settings
        sublime.set_timeout(lambda : in_main(ret_, err_), hide_delay if not only_async else 20)

    project.completion_context.running.insert(completion_id, (complete_offset, view.id()))
    project.completion_context.current_id = completion_id


    run_compiler_completion(on_result, True)


def create_completion_input_key (fn, offset, commas, src, macro_completion, complete_char, comp_type):
    return (fn,offset,commas,src[0:offset-1], macro_completion, complete_char, comp_type)


def use_completion_cache (last_input, current_input):
    return last_input is not None and current_input == last_input

def supported_compiler_completion_char (char):
    return char in "(.,"


def is_package_available (target, pack):
    cls = hxconfig
    res = True
    
    if target != None and pack in cls.target_packages:
        if target in cls.target_std_packages:
            if pack not in cls.target_std_packages[target]:
                res = False;

    return res

def get_toplevel_completion( project, src , build, is_macro_completion = False, only_types = False ) :
    cl = []
    packs = []
    std_packages = []

    
    build_target = "neko" if is_macro_completion else build.target

    if (only_types):
        comps = []
    else:
        comps = [("trace\ttoplevel","trace"),("this\ttoplevel","this"),("super\ttoplevel","super")]

    src = hxsrctools.comments.sub("",src)

    local_types = hxsrctools.type_decl.findall( src )
    for t in local_types :
        if t[1] not in cl:
            cl.append( t[1] )


    imports = hxsrctools.import_line.findall( src )
    imported = []
    for i in imports :
        imp = i[1]
        imported.append(imp)

    build_classes , build_packs = build.get_types()

    log("number of build classes: " + str(len(build_classes)))

    # filter duplicates
    def filter_build (x):
        for c in cl:
            if x == c:
                return False
        return True

    build_classes = filter(filter_build, build_classes)
    


    cl.extend( project.std_classes )
    
    cl.extend( build_classes )
    
    cl.sort();

    log("target: " + str(build_target))

    for p in project.std_packages :
        if is_package_available(build_target, p):
            if p == "flash9" or p == "flash8" :
                p = "flash"
            std_packages.append(p)

    packs.extend( std_packages )
    packs.extend( build_packs ) 
    if not only_types:
        for v in hxsrctools.variables.findall(src) :
            comps.append(( v + "\tvar" , v ))
    
        for f in hxsrctools.named_functions.findall(src) :
            if f not in ["new"] :
                comps.append(( f + "\tfunction" , f ))
        #TODO can we restrict this to local scope ?
        for params_text in hxsrctools.function_params.findall(src) :
            cleaned_params_text = re.sub(hxsrctools.param_default,"",params_text)
            params_list = cleaned_params_text.split(",")
            for param in params_list:
                a = param.strip();
                if a.startswith("?"):
                    a = a[1:]
                
                idx = a.find(":") 
                if idx > -1:
                    a = a[0:idx]

                idx = a.find("=")
                if idx > -1:
                    a = a[0:idx]
                    
                a = a.strip()
                cm = (a + "\tvar", a)
                if cm not in comps:
                    comps.append( cm )

    for c in cl :
        spl = c.split(".")
        if spl[0] == "flash9" or spl[0] == "flash8" :
            spl[0] = "flash"

        if c in hxconfig.ignored_types:
            continue

        top = spl[0]
        
        clname = spl.pop()
        enum_name = None;

        if len(spl) >= 2:
            last1 = spl[len(spl)-2]
            last2 = spl[len(spl)-1]

            if last1[0].isupper():
                enum_name = last2
                spl.pop()
                if enum_name == last1:
                    spl.pop();
                     
        pack = ".".join(spl)

        display = clname

        if enum_name is not None:
            spl.append(enum_name) 
            display = enum_name + "." + display

        if pack != "" :
            display += "\t" + pack
        else :
            display += "\tclass"
        
        
        
        spl.append(clname)
        
        is_imported = (pack in imported or c in imported 
                 or (enum_name != None and (pack + "." + enum_name) in imported))

        if is_imported:
           
            cm = ( display , clname )
            # at this point we could search for enum constructors and
            # add them to toplevel completion
        
        else :
            #add an option for full packages in completion, something like this:
            #cm = ( ".".join(spl) , ".".join(spl) )
            
            cm = ( display , ".".join(spl) )

        if cm not in comps and is_package_available(build_target, top):
            # add packages to completion
            
            z = [x for x in spl if len(x) > 0 and x[0].lower() == x[0]]
            if (len(z) > 0):
                p = ".".join(z)
                packs.append(p) 

            comps.append( cm )
        
    
    for p in packs :
        cm = (p + "\tpackage",p)
        if cm not in comps :
            comps.append(cm)

    #log("comps:" + str(comps))
    return comps



def highlight_errors( errors , view ) :
    regions = []
    
    for e in errors :
        
        l = e["line"]
        left = e["from"]
        right = e["to"]
        a = view.text_point(l,left)
        b = view.text_point(l,right)

        regions.append( sublime.Region(a,b))

        
        hxpanel.default_panel().status( "Error" , e["file"] + ":" + str(l) + ": characters " + str(left) + "-" + str(right) + ": " + e["message"])

            
    view.add_regions("haxe-error" , regions , "invalid" , "dot" )


def count_commas_and_complete_offset (src, prev_comma, complete_offset):
    commas = 0;
    closed_pars = 0
    closed_braces = 0
    closed_brackets = 0

    for i in range( prev_comma , 0 , -1 ) :
        c = src[i]
        if c == ")" :
            closed_pars += 1
        elif c == "(" :
            if closed_pars < 1 :
                complete_offset = i+1
                break
            else :
                closed_pars -= 1
        elif c == "," :
            if closed_pars == 0 and closed_braces == 0 and closed_brackets == 0 :
                commas += 1
        elif c == "{" :
            #commas = 0
            closed_braces -= 1

        elif c == "}" :
            closed_braces += 1
        elif c == "[" :
            #commas = 0
            closed_brackets -= 1
        elif c == "]" :
            closed_brackets += 1

    return (commas, complete_offset)


def get_completion_info (view, offset, src):
    prev = src[offset-1]
    commas = 0
    
    complete_offset = offset
    is_new = False
    prev_symbol_is_comma = False
    if (prev == " " and (offset-4 >= 0) and src[offset-4:offset-1] == "new"):
        is_new = True
    elif prev not in "(." :
        fragment = view.substr(sublime.Region(0,offset))
        prev_dot = fragment.rfind(".")
        prev_par = fragment.rfind("(")
        prev_comma = fragment.rfind(",")
        prev_colon = fragment.rfind(":")
        prev_brace = fragment.rfind("{")
        
        prev_symbol = max(prev_dot,prev_par,prev_comma,prev_brace,prev_colon)
        
        if prev_symbol == prev_comma:
            commas, complete_offset = count_commas_and_complete_offset(src, prev_comma, complete_offset)
            log("commas: " + str(commas))
            #print("closedBrackets : " + str(closedBrackets))
            prev_symbol_is_comma = True
        else :

            complete_offset = max( prev_dot + 1, prev_par + 1 , prev_colon + 1 )
            

    return (commas, complete_offset, prev_symbol_is_comma, is_new)

class CompletionInfo:

    def __init__(self, commas, complete_offset, toplevel_complete, is_new):
        self.commas = commas
        self.complete_offset = complete_offset
        self.toplevel_complete = toplevel_complete
        self.is_new = is_new


def cancel_completion(view, hide_complete = True):
    if hide_complete:
        # this seems to work fine, it cancels the sublime
        # triggered completion without poping up a completion
        # view
        view.run_command('hide_auto_complete')
    return [("  ...  ", "")]

def trigger_manual_completion(view, macro_completion):
    
    def run_complete():
        if (macro_completion):
            view.run_command("haxe_display_macro_completion")
        else:
            view.run_command("haxe_display_completion")

    sublime.set_timeout(run_complete, 20)

def trigger_manual_completion_type(view, comp_type):
    
    def run_complete():
        if (comp_type == "hint"):
            view.run_command("haxe_hint_display_completion")
        else:
            view.run_command("haxe_display_completion")

    sublime.set_timeout(run_complete, 20)
    

def get_compiler_completion( project, build, view , display, temp_file, orig_file, async, cb, macroCompletion = False, comp_type = "normal") :
        
    server_mode = project.is_server_mode()
    

    project.completion_context.set_errors([])

    build.set_auto_completion(display, macroCompletion)
    
    if hxsettings.show_completion_times(view):
        build.set_times()

    haxe_exec = project.haxe_exec(view)
    env = project.haxe_env(view)

    if (async):
        
        build.run_async(haxe_exec, env, server_mode, view, project, cb)
    else:
        out, err = build.run(haxe_exec, env, server_mode, view, project)
        cb(out, err)


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
        handler = hxml_auto_complete
    elif hxconfig.SOURCE_HAXE in scopes : # hx can be hxsl or haxe
        if view_tools.is_hxsl(view) :
            handler = hxsl_auto_complete # hxsl completion
        else :
            handler = hx_auto_complete # hx completion
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


# EventListener are created once by sublime at start
class HaxeCompleteListener( sublime_plugin.EventListener ):

    def __del__( self ) :
        hxproject.destroy()

    def on_load( self, view ) :

        if view is not None and view.file_name() is not None and view_tools.is_supported(view): 
            if not hxproject.current_project(view).has_build():
                hxproject.current_project(view).generate_build( view )


    def on_post_save( self , view ) :
        if view is not None and view.file_name() is not None and view_tools.is_hxml(view):
            project = hxproject.current_project(view)
            project.clear_build()
            
    # if view is None it's a preview
    def on_activated( self , view ) :
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
        log("on_query_completions triggered")

        project = hxproject.current_project(view)
        return dispatch_auto_complete(project, view, prefix, locations[0])
        
