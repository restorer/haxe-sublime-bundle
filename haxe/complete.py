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


# ------------------- HX COMPLETION -------------------------


# ------------------- DATA ----------------------------------

def lazyprop(fn):
    attr_name = '_lazy_' + fn.__name__
    @property
    def _lazyprop(self):
        if not hasattr(self, attr_name):
            setattr(self, attr_name, fn(self))
        return getattr(self, attr_name)
    return _lazyprop

COMPLETION_TRIGGER_MANUAL = 1
COMPLETION_TRIGGER_AUTO = 2

COMPILER_CONTEXT_MACRO = 1
COMPILER_CONTEXT_REGULAR = 2

COMPLETION_TYPE_REGULAR = 1 # regular compiler completion without hints
COMPLETION_TYPE_HINT = 2 # compiler hints
COMPLETION_TYPE_TOPLEVEL = 4 # include top level if useful
COMPLETION_TYPE_TOPLEVEL_FORCED = COMPLETION_TYPE_TOPLEVEL | 8 # force inclusion of top level completion

TOPLEVEL_OPTION_TYPES = 1
TOPLEVEL_OPTION_LOCALS = 2
TOPLEVEL_OPTION_KEYWORDS = 4

TOPLEVEL_OPTION_ALL = TOPLEVEL_OPTION_KEYWORDS | TOPLEVEL_OPTION_LOCALS | TOPLEVEL_OPTION_TYPES



class CompletionOptions:
    def __init__(self, trigger, context = COMPILER_CONTEXT_REGULAR, types = COMPLETION_TYPE_REGULAR, toplevel = 0):
        self._types = CompletionTypes(types)
        self._toplevel = TopLevelOptions(toplevel)
        self._context = context
        self._trigger = trigger
    @property
    def types(self):
        return self._types

    @lazyprop
    def manual_completion(self):
        return self._trigger == COMPLETION_TRIGGER_MANUAL

    @lazyprop
    def macro_completion(self):
        return self._context == COMPILER_CONTEXT_MACRO

    @lazyprop
    def regular_completion(self):
        return self._context == COMPILER_CONTEXT_REGULAR

    def eq (self, other):
        return self._trigger == other._trigger and self._types.eq(other._types) and self._toplevel.eq(other._toplevel) and self._context == other._context


class CompletionTypes:

    def __init__(self, val = COMPLETION_TYPE_REGULAR):
        self._opt = val

    def add (self, val):
        self._opt |= val

    def has_regular (self):
        return (self._opt & COMPLETION_TYPE_REGULAR) > 0

    def has_hint (self):
        return (self._opt & COMPLETION_TYPE_HINT) > 0
    
    def has_toplevel (self):
        return (self._opt & COMPLETION_TYPE_TOPLEVEL) > 0

    def has_toplevel_forced (self):
        return (self._opt & COMPLETION_TYPE_TOPLEVEL_FORCED) > 0

    def eq (self, other):
        return self._opt == other._opt

class TopLevelOptions:

    def __init__(self, val = 0):
        self._opt = val

    def set (self, val):
        self._opt |= val

    def hasTypes (self):
        return (self._opt & TOPLEVEL_OPTION_TYPES) > 0

    def hasLocals (self):
        return (self._opt & TOPLEVEL_OPTION_LOCALS) > 0
    
    def hasKeywords (self):
        return (self._opt & TOPLEVEL_OPTION_KEYWORDS) > 0

    def eq (self, other):
        return self._opt == other._opt

class CompletionSettings:
    def __init__(self, settings):
        self.settings = settings

    @lazyprop
    def smarts_hints_only_next(self):
        return self.settings.smarts_hints_only_next()

    @lazyprop
    def no_fuzzy_completion(self):
        return self.settings.no_fuzzy_completion()

    @lazyprop
    def top_level_completions_only_on_demand(self):
        return self.settings.top_level_completions_on_demand()

    @lazyprop
    def is_async_completion(self):
        return self.settings.is_async_completion()

    @lazyprop
    def show_only_async_completions(self):
        return self.settings.show_only_async_completions()

    @lazyprop
    def get_completion_delays(self):
        return self.settings.get_completion_delays()

    def show_completion_times(self, view):
        return self.settings.show_completion_times(view)

#
#class CompletionResult:
#    def __init__(self, toplevel, comps, hints, options, errors):
#        self.toplevel = toplevel
#        self.comps = comps
#        self.hints = hints
#        self.errors = errors
#        self.options = options
#
#    def to_sublime_completions (self):
#        res = []
#
#        if self.options.types.hasHint():     res.extend(hints_to_sublime_completions(self.hints))
#        if self.options.types.hasToplevel(): res.extend(self.toplevel)
#        if self.options.types.hasRegular():  res.extend(self.comps)
#
#        return res


class CompletionContext:
    def __init__(self, view, project, offset, options, settings):
        self.view = view

        # position in src where auto completion was triggered
        self.offset = offset
    
        # current project
        self.project = project
        
        # context independent completion options
        self.options = options

        # user settings
        self.settings = settings

    @lazyprop
    def id(self):
        return get_completion_id()

    @lazyprop
    def orig_file(self):
        return self.view.file_name()

    # build which is used for current compiler completion
    @lazyprop
    def build(self):
        if not self.project.has_build():
            self.project.extract_build_args()
        return self.project.get_build( self.view ).copy()

    # indicates if completion starts after the first ( after a control struct like while, if, for etc.
    @lazyprop
    def complete_char_is_after_control_struct(self):
        return self.in_control_struct and self.control_char == "("

    @lazyprop
    def in_control_struct(self):
        return control_struct.search( self.src_until_complete_offset ) is not None

    @lazyprop
    def src_until_complete_offset(self):
        return self.src[0:self.complete_offset]

    # src of current file
    @lazyprop
    def src (self):
        return view_tools.get_content(self.view)

    @lazyprop
    def complete_char (self):
        return self.src[self.complete_offset-1]

    @lazyprop
    def src_from_complete_to_offset(self):
        return self.src[self.complete_offset:self.offset]

    @lazyprop
    def offset_char (self):
        return self.src[self.offset]

    @lazyprop
    def _completion_info(self):
        log("CALLED ONCE")
        return get_completion_info(self.view, self.offset, self.src)

    @lazyprop
    def commas(self):
        return self._completion_info[0]

    @lazyprop
    def prev_symbol_is_comma(self):
        return self._completion_info[2]

    # position in source where compiler completion gets triggered
    @lazyprop
    def complete_offset(self):
        return self._completion_info[1]

    @lazyprop
    def is_new(self):
        return self._completion_info[3]

    @lazyprop
    def src_until_offset (self):
        return self.src[0:self.offset-1]

    @lazyprop
    def temp_completion_src(self):
        return self.src[:self.complete_offset] + "|" + self.src[self.complete_offset:]


    def eq (self, other):
        return (
            self != None and other != None
        and self.orig_file == other.orig_file
        and self.offset == other.offset
        and self.commas == other.commas
        and self.src_until_offset == other.src_until_offset
        and self.options.eq(other.options)
        and self.complete_char == other.complete_char)



# ------------------- FUNCTIONS ----------------------------------

def get_completions_from_background_run(background_result, view):

    ctx = background_result.ctx

    has_results = background_result.has_results()

    log("has_bg_results: " + str(has_results))

    comps = None

    if (not has_results and (hxsettings.no_fuzzy_completion() or ctx.options.types.has_hint())):
        comps = cancel_completion(view)
    else:
        comps = combine_hints_and_comps(background_result)

    return comps


def hx_auto_complete(project, view, offset):

    # if completion is triggered by a background completion process
    # completion return the result
    background_result = project.completion_context.get_and_delete_async(view)

    if background_result is not None:
        comps = get_completions_from_background_run(background_result, view)
    else:
        # get build and maybe use cache
        comps = get_completions_regular(project, view, offset)
    return comps

def filter_top_level_completions (offset_char, all_comps):
        
    comps = []

    is_lower = offset_char in "abcdefghijklmnopqrstuvwxyz"
    is_upper = offset_char in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    is_digit = offset_char in "0123456789"
    is_special = offset_char in "$_#"
    
    if is_lower or is_upper or is_digit or is_special:
        offset_upper = offset_char.upper()
        offset_lower = offset_char.lower()

        for c in all_comps:

            id = c[1]

            if (offset_char in id
                or (is_upper and offset_lower in id)
                or (is_lower and offset_upper in id)):
                comps.append(c)
    else:
        comps = all_comps

    log("number of top level completions (all: " + str(len(all_comps)) + ", filtered: " + str(len(comps)) + ")")
    return comps


def hints_to_sublime_completions(hints):
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

    return [make_hint_comp(h) for h in hints]

def combine_hints_and_comps (comp_result):
    all_comps = hints_to_sublime_completions(comp_result.hints)

    if not comp_result.ctx.options.types.has_hint() or len(comp_result.hints) == 0:
        all_comps.extend(comp_result.all_comps())
    return all_comps

def get_completions_regular(project, view, offset):
    
    cache = project.completion_context.current
    
    return hx_normal_auto_complete(project, view, offset, cache)

def is_iterator_completion(src, offset):
    o = offset
    s = src
    return o > 3 and s[o] == "\n" and s[o-1] == "." and s[o-2] == "." and s[o-3] != "."

def should_trigger_manual_hint_completion(manual_completion, complete_char):
    return not manual_completion and complete_char in "(,"


def is_same_completion_already_running(ctx):
    project = ctx.project
    complete_offset = ctx.complete_offset
    view = ctx.view

    last_completion_id = project.completion_context.current_id
    running_completion = project.completion_context.running.get_or_default(last_completion_id, None)    
    return running_completion is not None and running_completion[0] == complete_offset and running_completion[1] == view.id()

def should_include_top_level_completion(ctx):
    
    in_control_struct = ctx.in_control_struct
    

    toplevel_complete = ctx.complete_char in ":(,{;" or in_control_struct or ctx.is_new
    
    return toplevel_complete


def get_toplevel_completion_if_reasonable(ctx):
    if should_include_top_level_completion( ctx ):
        all_comps = get_toplevel_completion( ctx )
        comps = filter_top_level_completions(ctx.offset_char, all_comps)
    else:
        comps = []
    return comps


def get_completion_id ():
    # make the current time the id for this completion
    return time.time()

def hx_normal_auto_complete(project, view, offset, cache):

    trigger = project.completion_context.get_and_delete_trigger(view)
    comp_type = project.completion_context.get_and_delete_trigger_comp(view)
    
    manual_completion = trigger is not hxproject.TRIGGER_SUBLIME

    macro_completion = trigger is hxproject.TRIGGER_MANUAL_MACRO


    log("is macro completion :" + str(macro_completion))
    compiler_context = COMPILER_CONTEXT_MACRO if macro_completion else COMPLETION_TYPE_REGULAR
    completion_type = COMPLETION_TYPE_REGULAR if comp_type != "hint" else COMPLETION_TYPE_HINT
    completion_type |= COMPLETION_TYPE_TOPLEVEL

    completion_trigger = COMPLETION_TRIGGER_MANUAL if manual_completion else COMPLETION_TRIGGER_AUTO

    options = CompletionOptions(completion_trigger, compiler_context, completion_type, TOPLEVEL_OPTION_ALL)
    settings = CompletionSettings(hxsettings)
    ctx = CompletionContext(view, project, offset, options, settings)


    log("------- COMPLETION START -----------")


    #src_dir = os.path.dirname(orig_file)
    
    is_new = ctx.is_new

    #commas, complete_offset, prev_symbol_is_comma, is_new = get_completion_info(view, offset, src)
    
    complete_char = ctx.complete_char

    log("comp_type:" + comp_type)
    log("src:" + str(ctx.src))
    log("completion_info:" + str(ctx._completion_info))
    log("complete_offset:" + str(ctx.complete_offset))
    
    log("complete_char:" + complete_char)

    res = None
    
    # autocompletion is triggered, but its already 
    # running as a background process, starting it
    # again would result in multiple queries for
    # the same view and src position
    if is_same_completion_already_running(ctx):
        log("cancel completion, same is running")
        res = cancel_completion(ctx.view)
    elif should_trigger_manual_hint_completion(ctx.options.manual_completion, ctx.complete_char):
        trigger_manual_completion_type(ctx.view, "hint")
        res = cancel_completion(ctx.view)
    elif not manual_completion:
        trigger_manual_completion(ctx.view, macro_completion )
        res = cancel_completion(ctx.view)
    elif is_iterator_completion(ctx.src, ctx.offset):
        log("iterator completion")
        res = [(".\tint iterator", "..")]
    else:
    
        #toplevel_complete = should_include_top_level_completion(src, comp_type, is_new, complete_offset, offset, prev_symbol_is_comma, on_demand, in_control_struct, complete_char)
        
        src_until_completion_offset = ctx.src_until_complete_offset

        in_control_struct = control_struct.search( src_until_completion_offset ) is not None

        is_directly_after_control_struct = ctx.complete_char_is_after_control_struct


        #comp_type != "hint" and (is_new or (toplevel_complete and (in_control_struct or complete_char not in "(,")))
        only_top_level = is_new or is_directly_after_control_struct
        #log("is_after_cs: " + str(is_directly_after_control_struct))




        log("only_top_level: " + str(only_top_level))
        log("in_control_struct: " + str(in_control_struct))

        def get_toplevel_completions (): 
            return get_toplevel_completion_if_reasonable(ctx)

        if only_top_level:
            log("is_new or is_directly_after_control_struct")
            log("is_after_cs: " + str(is_directly_after_control_struct))
            log("is new: " + str(is_new))
            res = get_toplevel_completions()
        else:

            last_ctx = cache["input"]

            if use_completion_cache(ctx,last_ctx) :
                log("USE COMPLETION CACHE")
                out = cache["output"]

                res = combine_hints_and_comps(out)
            else :
                
                toplevel_comps = get_toplevel_completions()
                async = hxsettings.is_async_completion()

                log("USE ASYNC COMPLETION: " + str(async))

                comp_result = get_fresh_completions(ctx, toplevel_comps, cache)
                comp_result.toplevel = toplevel_comps


                if async and hxsettings.show_only_async_completions() and supported_compiler_completion_char(complete_char):
                    # we don't show any completions at this point
                    res = cancel_completion(view, True)
                else:
                    if not async:
                        update_completion_cache(cache, comp_result)
                    

                    res = combine_hints_and_comps(comp_result)
    return res


class CompletionResult:
    @staticmethod
    def empty_result (ctx):
        return CompletionResult("", [], "", [], [], ctx)


    def __init__(self, ret, comps, status, hints, toplevel, ctx):
        self.ret = ret
        self.comps = comps
        self.status = status
        self.hints = hints
        self.ctx = ctx
        self.toplevel = toplevel

    def has_results (self):
        return len(self.comps) > 0 or len(self.hints) > 0 or len(self.toplevel) > 0

    def all_comps (self):
        res = list(self.toplevel)
        res.extend(self.comps)
        return res


def update_completion_cache(cache, comp_result):
    cache["output"] = comp_result
    cache["input"] = comp_result.ctx

def log_completion_status(status, comps, hints):
    if status != "":
        if len(comps) > 0 or len(hints) > 0:
            log(status)
        else:
            hxpanel.default_panel().writeln( status )    

def get_fresh_completions(ctx, toplevel_comps, cache):
    
    complete_char = ctx.complete_char
    build = ctx.build
    orig_file = ctx.orig_file
    async = ctx.settings.is_async_completion
    if supported_compiler_completion_char(complete_char): 
        log(build)

        tmp_src = ctx.temp_completion_src

        temp_path, temp_file = hxtemp.create_temp_path_and_file(build, orig_file, tmp_src)

        res = None

        if temp_path is None or temp_file is None:
            # this should never happen, todo proper error message
            log("completion error")
            res = CompletionResult.empty_result(ctx)
        else:

            build.add_classpath(temp_path)
            display = temp_file + "@0"
            def run_compiler_completion (cb):
                return get_compiler_completion( ctx, display, cb )
            if async:
                log("run async compiler completion")

                run_async_completion(ctx, list(toplevel_comps), temp_file, temp_path,
                    cache, run_compiler_completion)
                
                res = CompletionResult.empty_result(ctx)
            else:
                log("run normal compiler completion")
                ret0 = []
                err0 = []
                def cb(out1, err1):
                    ret0.append(out1)
                    err0.append(err1)
                run_compiler_completion(cb)
                ret = ret0[0]
                err = err0[0]
                
                hxtemp.remove_path(temp_path)
                
                res = output_to_result(ctx, temp_file, err, ret, [])
    else:
        log("not supported completion char")
        res = CompletionResult.empty_result(ctx)

    return res


def output_to_result (ctx, temp_file, err, ret, toplevel_comps):
    hints, comps1, status, errors = get_completion_output(temp_file, ctx.orig_file, err, ctx.commas)
    # we don't need doc here
    comps1 = [(t.hint, t.insert) for t in comps1]
    ctx.project.completion_context.set_errors(errors)
    highlight_errors( errors, ctx.view )
    return CompletionResult(ret, comps1, status, hints, toplevel_comps, ctx )

def async_completion_finished(ctx, ret_, err_, temp_file, temp_path, toplevel_comps, cache, view_id):
    
    show_delay = ctx.settings.get_completion_delays[1]
    project = ctx.project
    view = ctx.view
    only_async = ctx.settings.show_only_async_completions
    macro_completion = ctx.options.macro_completion
    completion_id = ctx.id

    if completion_id == project.completion_context.current_id:

        hxtemp.remove_path(temp_path)

        comp_result = output_to_result(ctx, temp_file, err_, ret_, list(toplevel_comps))
        update_completion_cache(cache, comp_result)

        # do we still need this completion, or is it old
        has_results = comp_result.has_results()
        
        if completion_id == project.completion_context.current_id and (has_results or hxsettings.show_only_async_completions()):
            
            project.completion_context.async.insert(view_id, comp_result)
            if only_async:
                log("trigger_auto_complete")
                if ctx.options.types.has_hint():
                    trigger_manual_completion_type(view,"hint")
                else:
                    trigger_manual_completion(view,macro_completion)
            else:
                view.run_command('hide_auto_complete')
                sublime.set_timeout(lambda : trigger_manual_completion(view,macro_completion), show_delay)
        else:
            log("ignore background completion")    
    else:
        log("ignore background completion")
    
    project.completion_context.running.delete(completion_id)


def run_async_completion(ctx, toplevel_comps, temp_file, temp_path, 
        cache, run_compiler_completion):
    
    project = ctx.project
    complete_offset = ctx.complete_offset
    hide_delay = ctx.settings.get_completion_delays[0]
    view_id = ctx.view.id()
    only_async = hxsettings.show_only_async_completions()

    start_time = time.time()

    def in_main (ret_, err_):
        run_time = time.time() - start_time;
        log("async completion time: " + str(run_time))

        async_completion_finished(ctx, ret_, err_, temp_file, temp_path, toplevel_comps, cache, view_id)
        
    def on_result(ret_, err_):
        # replace current completion workaround
        # delays are customizable with project settings
        sublime.set_timeout(lambda : in_main(ret_, err_), hide_delay if not only_async else 20)

    project.completion_context.running.insert(ctx.id, (complete_offset, view_id))
    project.completion_context.current_id = ctx.id


    run_compiler_completion(on_result)



def use_completion_cache (last_input, current_input):
    return last_input.eq(current_input)

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

def get_toplevel_completion( ctx  ) :
    
    project = ctx.project
    src = ctx.src 
    build = ctx.build.copy()
    is_macro_completion = ctx.options.macro_completion
    only_types = ctx.is_new
    
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
    elif prev not in "(.;" :
        fragment = view.substr(sublime.Region(0,offset))
        prev_dot = fragment.rfind(".")
        prev_par = fragment.rfind("(")
        prev_comma = fragment.rfind(",")
        prev_colon = fragment.rfind(":")
        prev_brace = fragment.rfind("{")
        prev_semi = fragment.rfind(";")
        
        
        prev_symbol = max(prev_dot,prev_par,prev_comma,prev_brace,prev_colon, prev_semi)
        
        if prev_symbol == prev_comma:
            commas, complete_offset = count_commas_and_complete_offset(src, prev_comma, complete_offset)
            #print("closedBrackets : " + str(closedBrackets))
            prev_symbol_is_comma = True
        else :
            complete_offset = max( prev_dot + 1, prev_par + 1 , prev_colon + 1, prev_brace + 1, prev_semi + 1 )
            

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
    

def get_compiler_completion( ctx , display, cb) :
    project = ctx.project
    build = ctx.build
    view = ctx.view
    macroCompletion = ctx.options.macro_completion
    async = ctx.settings.is_async_completion

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
        
