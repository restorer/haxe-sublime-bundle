import time
import sublime

is_st3 = int(sublime.version()) >= 3000

if is_st3:
    import Haxe.haxe.settings as hxsettings
    import Haxe.haxe.panel as hxpanel
    import Haxe.haxe.completion.hx.toplevel as toplevel
    import Haxe.haxe.temp as hxtemp
    from Haxe.haxe.completion.hx.types import CompletionOptions, CompletionSettings, CompletionContext, CompletionResult, CompletionBuild
    import Haxe.haxe.completion.hx.constants as hxconst
    from Haxe.haxe.compiler.output import get_completion_output
    from Haxe.haxe.log import log
else:
    import haxe.settings as hxsettings
    import haxe.panel as hxpanel
    import haxe.completion.hx.toplevel as toplevel
    import haxe.temp as hxtemp
    from haxe.completion.hx.types import CompletionOptions, CompletionSettings, CompletionContext, CompletionResult, CompletionBuild
    import haxe.completion.hx.constants as hxconst
    from haxe.compiler.output import get_completion_output
    from haxe.log import log


# ------------------- FUNCTIONS ----------------------------------




def get_async_completions(comp_result, view):

    ctx = comp_result.ctx

    has_results = comp_result.has_results()

    comps = None

    if (not has_results and (hxsettings.no_fuzzy_completion() or ctx.options.types.has_hint())):
        comps = cancel_completion(view)
    else:
        comps = combine_hints_and_comps(comp_result)

    return comps


def auto_complete(project, view, offset):

    # if completion is triggered by a background completion process
    # completion return the result
    async_result = project.completion_context.get_and_delete_async(view)

    if async_result is not None and async_result.has_results():
        comps = get_async_completions(async_result, view)
    else:
        # get build and maybe use cache
        comps = get_completions_regular(project, view, offset)
    return comps

def get_completions_regular(project, view, offset):
    
    cache = project.completion_context.current
    
    return hx_normal_auto_complete(project, view, offset, cache)


def hx_normal_auto_complete(project, view, offset, cache):

    log("------- COMPLETION START -----------")

    ctx = create_completion_context(project, view, offset)

    res = None
    
    # autocompletion is triggered, but its already 
    # running as a background process, starting it
    # again would result in multiple queries for
    # the same view and src position
    if is_equivalent_completion_already_running(ctx):
        log("cancel completion, same is running")
        res = cancel_completion(ctx.view)
    elif should_trigger_manual_hint_completion(ctx.options.manual_completion, ctx.complete_char):
        trigger_manual_completion(ctx.view, ctx.options.copy_as_manual())
        res = cancel_completion(ctx.view)
    elif not ctx.options.manual_completion:
        trigger_manual_completion(ctx.view, ctx.options.copy_as_manual() )
        res = cancel_completion(ctx.view)
    elif is_iterator_completion(ctx.src, ctx.offset):
        log("iterator completion")
        res = [(".\tint iterator", "..")]
    else:
    
        is_directly_after_control_struct = ctx.complete_char_is_after_control_struct

        only_top_level = ctx.is_new or is_directly_after_control_struct


        log("only_top_level: " + str(only_top_level))
        

        if only_top_level:
            res = get_toplevel_completions(ctx)
        else:

            last_ctx = cache["input"]

            if use_completion_cache(ctx,last_ctx) :
                log("USE COMPLETION CACHE")
                out = cache["output"]
                res = combine_hints_and_comps(out)
            else :
                
                if supported_compiler_completion_char(ctx.complete_char):

                    toplevel_comps = get_toplevel_completions(ctx)
                    
                    comp_result = get_fresh_completions(ctx, toplevel_comps, cache)
                    
                    # we don't show any completions at this point
                    res = cancel_completion(view, True)
                else:
                    toplevel_comps = get_toplevel_completions(ctx)
                    comp_result = CompletionResult.empty_result(ctx)
                    comp_result.toplevel = toplevel_comps
                    res = combine_hints_and_comps(comp_result)
    return res

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
            
            res = (show, insert)
        return res

    return [make_hint_comp(h) for h in hints]

def combine_hints_and_comps (comp_result):
    all_comps = hints_to_sublime_completions(comp_result.hints)

    if not comp_result.ctx.options.types.has_hint() or len(comp_result.hints) == 0:
        all_comps.extend(comp_result.all_comps())
    return all_comps



def is_iterator_completion(src, offset):
    o = offset
    s = src
    return o > 3 and s[o] == "\n" and s[o-1] == "." and s[o-2] == "." and s[o-3] != "."

def should_trigger_manual_hint_completion(manual_completion, complete_char):
    return not manual_completion and complete_char in "(,"


def is_equivalent_completion_already_running(ctx):
    return ctx.project.completion_context.is_equivalent_completion_already_running(ctx)

def should_include_top_level_completion(ctx):
    

    toplevel_complete = ctx.complete_char in ":(,{;})" or ctx.in_control_struct or ctx.is_new
    
    return toplevel_complete


def get_toplevel_completions(ctx):
    if should_include_top_level_completion( ctx ):
        all_comps = toplevel.get_toplevel_completion( ctx )
        comps = toplevel.filter_top_level_completions(ctx.offset_char, all_comps)
    else:
        comps = []
    return comps


def create_completion_context(project, view, offset):
    options = project.completion_context.get_and_delete_trigger(view)

    # if options are None, it's a completion progress initialized by sublime, 
    # not by the user or by faking it
    if options == None:
        options = CompletionOptions(hxconst.COMPLETION_TRIGGER_AUTO)
    
    settings = CompletionSettings(hxsettings)
    ctx = CompletionContext(view, project, offset, options, settings)
    return ctx    





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
    
    tmp_src = ctx.temp_completion_src

    temp_path, temp_file = hxtemp.create_temp_path_and_file(ctx.build, ctx.orig_file, tmp_src)


    if temp_path is None or temp_file is None:
        # this should never happen, todo proper error message
        log("ERROR: cannot create temp_path or file")
    else:
        comp_build = CompletionBuild(ctx, temp_path, temp_file, toplevel_comps, cache)

        def cb (out, err):
            # remove temporary files
            hxtemp.remove_path(temp_path)
            completion_finished(comp_build, out, err)

        run_completion_async(comp_build, cb)

    return CompletionResult.empty_result(ctx)


def run_completion_async(comp_build, cb):
    ctx = comp_build.ctx
    project = ctx.project

    start_time = time.time()

    display = comp_build.display
    
    build = comp_build.build
    view = ctx.view

    comp_id = ctx.id

    macro_completion = ctx.options.macro_completion
    async = ctx.settings.is_async_completion

    def in_main (out, err):
        
        def run ():
            run_time = time.time() - start_time;
            log("completion time: " + str(run_time))
            cb(out, err)
        
        # because of async completion, the current completion could be 
        # out of date, because a newer completion was triggered, so run should
        # only be called if this completion is still up to date
        project.completion_context.run_if_still_up_to_date(comp_id, run)
        

    def on_result(out, err):
        sublime.set_timeout(lambda : in_main(out, err), 20)

    # store the data of the currently running completion operation in cache to fetch it later
    project.completion_context.set_new_completion(ctx);


    # prepare build options
    build.set_auto_completion(display, macro_completion)
    if ctx.settings.show_completion_times(view):
        build.set_times()

    build.run(project, view, async, on_result)


def completion_finished(comp_build, out, err):

    ctx = comp_build.ctx
    temp_file = comp_build.temp_file
    toplevel_comps = comp_build.toplevel_comps
    cache = comp_build.cache

    project = ctx.project
    view = ctx.view
    

    comp_result = output_to_result(ctx, temp_file, err, out, list(toplevel_comps))
    update_completion_cache(cache, comp_result)

    # do we still need this completion, does it have any results
    has_results = comp_result.has_results()
    
    if has_results:
        project.completion_context.add_completion_result(comp_result)
        trigger_manual_completion(view, ctx.options)
    else:
        log("ignore background completion on finished")    


def output_to_result (ctx, temp_file, err, ret, toplevel_comps):
    hints, comps1, status, errors = get_completion_output(temp_file, ctx.orig_file, err, ctx.commas)
    # we don't need doc here
    comps1 = [(t.hint, t.insert) for t in comps1]
    ctx.project.completion_context.set_errors(errors)
    highlight_errors( errors, ctx.view )
    return CompletionResult(ret, comps1, status, hints, toplevel_comps, ctx )

def use_completion_cache (last_input, current_input):
    return last_input.eq(current_input)

def supported_compiler_completion_char (char):
    return char in "(.,"


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





def cancel_completion(view, hide_complete = True):
    if hide_complete:
        # this seems to work fine, it cancels the sublime
        # triggered completion without poping up a completion
        # view
        view.run_command('hide_auto_complete')
    return [("  ...  ", "")]

def trigger_manual_completion(view, options):
    
    log("LOG: " + str(options.types._opt))


    hint = options.types.has_hint()
    macro = options.macro_completion

    def run_complete():
        if hint and macro:
            view.run_command("haxe_hint_display_macro_completion")
        if hint:
            view.run_command("haxe_hint_display_completion")
        if macro:
            view.run_command("haxe_display_macro_completion")
        else:
            view.run_command("haxe_display_completion")

    sublime.set_timeout(run_complete, 20)

