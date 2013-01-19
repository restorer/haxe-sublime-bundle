import sublime, sublime_plugin
import time

import os

import re

import haxe.settings as hxsettings

import haxe.build as hxbuild
import haxe.lib as hxlib
import haxe.panel as hxpanel

from haxe.compiler.output import get_completion_output

from haxe.config import Config



import haxe.types as hxtypes

import thread

import haxe.project as hxproject
import haxe.hxtools as hxsourcetools

from haxe.tools import ViewTools, ScopeTools

import haxe.temp as temp
    


class CompletionContext:

    TRIGGER_SUBLIME = "auto_sublime"
    TRIGGER_MANUAL_MACRO = "manual_macro"
    TRIGGER_MANUAL_NORMAL = "manual_normal"

    def __init__(self):
        
        self.completion_running = {}
        self.trigger = {}
        
        self.current_completion_id = None   
        self.errors = []
        self.delayed_completions = {}
        self.currentCompletion = {
            "input" : None,
            "output" : None
        }


    def set_manual_trigger(self, view, macro):
        cls = CompletionContext
        t = cls.TRIGGER_MANUAL_MACRO if macro else cls.TRIGGER_MANUAL_NORMAL
        self.trigger[view.id()] = (t, time.time())

    def clear_completion (self):
        self.currentCompletion = {
            "inp" : None,
            "outp" : None
        }

    def set_errors (self, errors):
        self.errors = errors

    def get_and_delete_trigger(self, view):
        id = view.id() 
        now = time.time()
        trigger = CompletionContext.TRIGGER_SUBLIME
        
        trigger_dict = self.trigger

        if id in trigger_dict:
            data = trigger_dict[id]
            del trigger_dict[id]
            oldTime = data[1]
            
            if (now - oldTime) < 1000:
                trigger = data[0]

        return trigger


def log (msg):
    print msg

def slide_panel () : 
    return hxpanel.slide_panel()

def tab_panel () : 
    return hxpanel.tab_panel()

libFlag = re.compile("-lib\s+(.*?)")


controlStruct = re.compile( "\s*(if|switch|for|while)\($" );


bundleFile = __file__
bundlePath = os.path.abspath(bundleFile)
bundleDir = os.path.dirname(bundlePath)







def filter_top_level_completions (offsetChar, all_comps):
    print("number of top level completions all:" + str(len(all_comps)))
        
    comps = []

    isLower = offsetChar in "abcdefghijklmnopqrstuvwxyz"
    isUpper = offsetChar in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    isDigit = offsetChar in "0123456789"
    isSpecial = offsetChar in "$_"
    offsetUpper = offsetChar.upper()
    offsetLower = offsetChar.lower()
    if isLower or isUpper or isDigit or isSpecial:
        print "its in"
        
        for c in all_comps:
            id = c[1]

            if (offsetChar in id
                or (isUpper and offsetLower in id)
                or (isLower and offsetUpper in id)):
                comps.append(c)
        
    else:
        comps = all_comps

    print "number of top level completions filtered" + str(len(comps))
    return comps

def hx_auto_complete(project, view, offset):

    completion_id = time.time()
    last_completion_id = project.completion_context.current_completion_id
    
    # if completion is triggered by a background
    # completion return the result
    if is_delayed_completion(project, view):
        c = project.completion_context.delayed_completions[view.id()][0]
        del project.completion_context.delayed_completions[view.id()]
        comps = c
    else:
        # get build and maybe use cache
        build = project.get_build( view ).copy()
        cache = project.completion_context.currentCompletion
        
        
        
        comps = hx_normal_auto_complete(project, completion_id, last_completion_id, view, offset, build, cache)
    return comps

def hx_normal_auto_complete(project, completion_id, last_completion_id, view, offset, build, cache):
    
    trigger = project.completion_context.get_and_delete_trigger(view)
    


    manual_completion = trigger is not CompletionContext.TRIGGER_SUBLIME

    macro_completion = trigger is CompletionContext.TRIGGER_MANUAL_MACRO

    
    

    log("is manual completion: " + str(manual_completion))

    log("is macro completion: " + str(macro_completion))

    if (hxsettings.no_fuzzy_completion() and not manual_completion):
        log("trigger manual")
        trigger_manual_completion(project, view, macro_completion)
        
        return cancel_completion(view)
    
        


    src = ViewTools.get_content(view)
    orig_file = view.file_name()
    src_dir = os.path.dirname(orig_file)
    
    

    #find actual autocompletable char.
    prev = src[offset-1]
    
    commas, completeOffset, toplevelComplete = get_completion_info(view, offset, src, prev)
    
    temp_path, temp_file = temp.create_temp_path_and_file(build, orig_file, src)

    if temp_path is None or temp_file is None:
        # this should never happen, todo proper error message
        return []

    # autocompletion is triggered, but its already 
    # running as a background process, starting it
    # again would result in multiple queries for
    # the same view and src position
    if last_completion_id in project.completion_context.completion_running:
        o1, id1 = project.completion_context.completion_running[last_completion_id]
        if (o1 == completeOffset and id1 == view.id()):
            print "cancel completion, same is running"
            return cancel_completion(view, False)

    top_level_build = build.copy()
    build.add_classpath(temp_path)

    complete_char = src[completeOffset-1]
    in_control_struct = controlStruct.search( src[0:completeOffset] ) is not None

    on_demand = hxsettings.top_level_completions_on_demand()

    toplevelComplete = (toplevelComplete or complete_char in ":(," or in_control_struct) and not on_demand

    

    offsetChar = src[offset]
    

    if (offsetChar == "\n" and prev == "." and src[offset-2] == "." and src[offset-3] != "."):
        return [(".\tint iterator", "..")]

    comps = []

    if toplevelComplete :
        all_comps = get_toplevel_completion( project, src , src_dir , top_level_build )
        comps = filter_top_level_completions(offsetChar, all_comps)
    else:
        print "comps_from_not_top_level"
        comps = []
    
    

    if toplevelComplete and (in_control_struct or complete_char not in "(,")  :
        print "comps_from_not_top_level_and_control_struct"
        return comps


    delayed = hxsettings.is_delayed_completion()

    display = temp_file + "@" + str(offset)
    
    comps1 = []
    status = ""

    offset = completeOffset

    current_input = create_completion_input_key(orig_file, offset, commas, src, macro_completion, complete_char)

    def run_compiler_completion ():
        return get_compiler_completion( project, build, view, display, temp_file, orig_file , macro_completion )

    last_input = cache["input"]



    print "DELAYED COMPLETION: " + str(delayed)

    use_cache = use_completion_cache(last_input, current_input)

    if use_cache :
        log("use completions from cache")
        ret, comps1, status = cache["output"]
    else :

        if supported_compiler_completion_char(complete_char): 

            if delayed:
                print "run delayed compiler completion"
                background_completion(project, completion_id, list(comps), temp_file, orig_file,temp_path,
                    view, cache, current_input, completeOffset, run_compiler_completion)
                
                ret, comps1, status = "", [], ""
            else:
                print "run normal compiler completion"
                ret, err = run_compiler_completion()
                hints, comps1, status, errors = get_completion_output(temp_file, orig_file, err)
    
                highlight_errors( errors, view )
        else:
            print "not supported completion char"
            ret, comps1, status = "",[], ""

    if use_cache:
        print "use cache"
        comps = comps1
    else:
        print "not use cache"
        comps.extend(comps1)
        
    
    if use_cache or not delayed:
        temp.remove_path(temp_path)
        
        cache["output"] = (ret,comps1,status)
        cache["input"] = current_input
    
    tab_panel().status( "haxe-status" , status )

    
    if not use_cache and delayed and hxsettings.only_delayed_completions():
        log("delayed is running: completion cancelled")
        return cancel_completion(view, True)
    
    
    if len(comps) == 0 and hxsettings.no_fuzzy_completion():
        log("no fuzzy and 0: completion cancelled")
        return cancel_completion(view)

    log("completion end")
    return comps

def background_completion(project, completion_id, basic_comps, temp_file, orig_file, temp_path, 
        view, cache, current_input, completeOffset, run_compiler_completion):
    hide_delay, show_delay = hxsettings.get_completion_delays()

    
    view_id = view.id()
    
    comps = list(basic_comps) # make copy

    only_delayed = hxsettings.only_delayed_completions()

    timer = time.time()

    def in_main (ret_, err_):
        hints, comps_, status_, errors = get_completion_output(temp_file, orig_file, err_)
        print "background completion time: " + str(time.time() - timer)
        project.completion_context.set_errors(errors)
        highlight_errors( errors, view )

        
        print "do remove temp_path"
        temp.remove_path(temp_path)
        comps.extend(comps_)

        
        if completion_id == project.completion_context.current_completion_id:
            cache["output"] = (ret_,comps,status_)
            cache["input"] = current_input
        else:
            print "ignored completion"
        
        # do we still need this completion, or is it old
        has_new_comps = len(comps) > len(basic_comps)
        if completion_id == project.completion_context.current_completion_id and (has_new_comps or hxsettings.only_delayed_completions()):
            now = time.time()
            project.completion_context.delayed_completions[view_id] = (comps, now)
            if only_delayed:
                print "trigger_auto_complete"
                view.run_command('auto_complete', {'disable_auto_insert': True})
            else:
                view.run_command('hide_auto_complete')
                print "trigger_auto_complete"
                sublime.set_timeout(lambda : view.run_command('auto_complete', {'disable_auto_insert': True}), show_delay)
        else:
            log("ignore background completion")
        
        del project.completion_context.completion_running[completion_id]
    def in_thread():
        ret_, err_ = run_compiler_completion()

        # replace current completion workaround
        # delays are customizable with project settings
        
        sublime.set_timeout(lambda : in_main(ret_, err_), hide_delay if not only_delayed else 20)

    project.completion_context.completion_running[completion_id] = (completeOffset, view.id())
    project.completion_context.current_completion_id = completion_id

    thread.start_new_thread(in_thread, ())  



def create_completion_input_key (fn, offset, commas, src, macro_completion, complete_char):
    return (fn,offset,commas,src[0:offset-1], macro_completion, complete_char)


def use_completion_cache (last_input, current_input):
    return last_input is not None and current_input == last_input

def supported_compiler_completion_char (char):
    return char in "(.,"


def get_toplevel_completion( project, src , src_dir , build ) :
    cl = []
    packs = []
    stdPackages = []

    comps = [("trace\ttoplevel","trace"),("this\ttoplevel","this"),("super\ttoplevel","super")]

    src = hxsourcetools.comments.sub("",src)

    localTypes = hxsourcetools.typeDecl.findall( src )
    for t in localTypes :
        if t[1] not in cl:
            print "local" + str(t[1])
            cl.append( t[1] )


    packageClasses, subPacks = hxtypes.extract_types( src_dir, project.stdClasses, project.stdPackages )
    for c in packageClasses :
        if c not in cl:
            print "package" + str(c)
            cl.append( c )

    imports = hxsourcetools.importLine.findall( src )
    imported = []
    for i in imports :
        imp = i[1]
        imported.append(imp)
        #dot = imp.rfind(".")+1
        #clname = imp[dot:]
        #cl.append( clname )
        #print( i )

    #print cl

    print str(build.classpaths)

    buildClasses , buildPacks = build.get_types()



    # filter duplicates
    def filter_build (x):
        for c in cl:
            if x == c:
                return False
        return True

    buildClasses = filter(filter_build, buildClasses)
    

    tarPkg = None
    

    if build.target is not None :
        tarPkg = build.target
        if tarPkg == "swf9" :
            tarPkg = "flash"
        if tarPkg == "swf" :
            tarPkg = "flash"

    if build.nmml is not None :
        tarPkg = "flash"
    
    #for c in HaxeComplete.stdClasses :
    #   p = c.split(".")[0]
    #   if tarPkg is None or (p not in targetPackages) or (p == tarPkg) :
    #       cl.append(c)

    

    cl.extend( project.stdClasses )
    
    cl.extend( buildClasses )
    
    cl.sort();


    
    #print("target : "+build.target)
    for p in project.stdPackages :
        #print(p)
        if p == "flash9" or p == "flash8" :
            p = "flash"
    #   if tarPkg is None or (p not in targetPackages) or (p == tarPkg) :
        stdPackages.append(p)

    packs.extend( stdPackages )
    

    for v in hxsourcetools.variables.findall(src) :
        comps.append(( v + "\tvar" , v ))
    
    for f in hxsourcetools.functions.findall(src) :
        if f not in ["new"] :
            comps.append(( f + "\tfunction" , f ))

    
    #TODO can we restrict this to local scope ?
    for paramsText in hxsourcetools.functionParams.findall(src) :
        cleanedParamsText = re.sub(hxsourcetools.paramDefault,"",paramsText)
        paramsList = cleanedParamsText.split(",")
        for param in paramsList:
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

        top = spl[0]
        #print(spl)
        
        clname = spl.pop()
        pack = ".".join(spl)
        display = clname

        #if pack in imported:
        #   pack = ""

        if pack != "" :
            display += "\t" + pack
        else :
            display += "\tclass"
        
        spl.append(clname)
        
        if pack in imported or c in imported :
            cm = ( display , clname )
        else :
            cm = ( display , ".".join(spl) )
        if cm not in comps and tarPkg is None or (top not in Config.targetPackages) or (top == tarPkg) : #( build.target is None or (top not in HaxeBuild.targets) or (top == build.target) ) :
            comps.append( cm )
    
    for p in packs :
        cm = (p + "\tpackage",p)
        if cm not in comps :
            comps.append(cm)

    
    return comps

def hxsl_auto_complete( project, view , offset ) :
    comps = []
    for t in ["Float","Float2","Float3","Float4","Matrix","M44","M33","M34","M43","Texture","CubeTexture","Int","Color","include"] :
        comps.append( ( t , "hxsl Type" ) )
    return comps

def hxml_auto_complete( project, view , offset ) :
    src = view.substr(sublime.Region(0, offset))
    currentLine = src[src.rfind("\n")+1:offset]
    m = libFlag.match( currentLine )
    if m is not None :
        return hxlib.HaxeLib.get_completions()
    else :
        return []


def highlight_errors( errors , view ) :
    print "highlight_errors" + str(len(errors))
    fn = view.file_name()
    regions = []
    


    for e in errors :
        if fn.endswith(e["file"]) :
            l = e["line"]
            left = e["from"]
            right = e["to"]
            a = view.text_point(l,left)
            b = view.text_point(l,right)

            regions.append( sublime.Region(a,b))

            
            slide_panel().status( "haxe-status" , "Error: " + e["message"] )
            
    view.add_regions("haxe-error" , regions , "invalid" , "dot" )


def count_commas_and_complete_offset (src, prevComa, completeOffset):
    commas = 0;
    closedPars = 0
    closedBrackets = 0

    for i in range( prevComa , 0 , -1 ) :
        c = src[i]
        if c == ")" :
            closedPars += 1
        elif c == "(" :
            if closedPars < 1 :
                completeOffset = i+1
                break
            else :
                closedPars -= 1
        elif c == "," :
            if closedPars == 0 :
                commas += 1
        elif c == "{" : # TODO : check for { ... , ... , ... } to have the right comma count
            commas = 0
            closedBrackets -= 1
        elif c == "}" :
            closedBrackets += 1

    return (commas, completeOffset)

def get_completion_info (view, offset, src, prev):
    commas = 0
    toplevelComplete = False
    completeOffset = offset
    if prev not in "(." :
        fragment = view.substr(sublime.Region(0,offset))
        prevDot = fragment.rfind(".")
        prevPar = fragment.rfind("(")
        prevComa = fragment.rfind(",")
        prevColon = fragment.rfind(":")
        prevBrace = fragment.rfind("{")
        prevSymbol = max(prevDot,prevPar,prevComa,prevBrace,prevColon)
        
        if prevSymbol == prevComa:
            commas, completeOffset = count_commas_and_complete_offset(src, prevComa, completeOffset)
            #print("closedBrackets : " + str(closedBrackets))
            
        else :

            completeOffset = max( prevDot + 1, prevPar + 1 , prevColon + 1 )
            skipped = src[completeOffset:offset]
            toplevelComplete = hxsourcetools.skippable.search( skipped ) is None and hxsourcetools.inAnonymous.search( skipped ) is None

    return (commas, completeOffset, toplevelComplete)


def run_nme( view, build ) :

    cmd = [ hxsettings.haxelib_exec(), "run", "nme", hxbuild.HaxeBuild.nme_target[2], os.path.basename(build.nmml) ]
    target = hxbuild.HaxeBuild.nme_target[1].split(" ")
    cmd.extend(target)
    cmd.append("-debug")

    view.window().run_command("exec", {
        "cmd": cmd,
        "working_dir": os.path.dirname(build.nmml),
        "file_regex": "^([^:]*):([0-9]+): characters [0-9]+-([0-9]+) :.*$"
    })
    return ("" , [], "" )



def is_delayed_completion(project, view):
    id = view.id() 
    now = time.time()
    delayed = False
    
    if id in project.completion_context.delayed_completions:
        oldTime = project.completion_context.delayed_completions[id][1]
        
        print "check times"
        if (now - oldTime) < 1000:
            delayed = True

    print "is delayed:" + str(delayed)
    return delayed

def cancel_completion(view, hide_complete = True):
    if hide_complete:
        # this seems to work fine, it cancels the current
        # triggered completion without poping up a completion
        # view
        view.run_command('hide_auto_complete')
    return [("  ...  ", "")]

def trigger_manual_completion(project, view, macro_completion):
    
    def run_complete():
        if (macro_completion):
            view.run_command("haxe_display_macro_completion")
        else:
            view.run_command("haxe_display_completion")
        

    sublime.set_timeout(run_complete, 20)
    



def get_compiler_completion( project, build, view , display, temp_file, orig_file, macroCompletion = False ) :
        
    server_mode = project.is_server_mode()
    

    project.completion_context.set_errors([])

    build.set_auto_completion(display, macroCompletion)
    
    if hxsettings.show_completion_times(view):
        build.set_times()



    build.set_build_cwd()


    haxe_exec = hxsettings.haxe_exec(view)

    return build.run(haxe_exec, server_mode, view, project)


# triggered from event
def auto_complete (project, view, prefix, locations):
    start_time = time.time()

    pos = locations[0]
    
    offset = pos - len(prefix)

    comps =  []

    if offset == 0 : 
        return comps 
    
    scopes = ViewTools.get_scopes_at(view, pos)

    if (ScopeTools.contains_string_or_comment(scopes)):
        return comps

    if Config.SOURCE_HXML in scopes:
        comps = hxml_auto_complete( project, view , offset )
    
    if Config.SOURCE_HAXE in scopes :
        if ViewTools.is_hxsl(view) :
            comps = hxsl_auto_complete( project, view , offset )
        else :
            comps = hx_auto_complete(project, view, offset) 
            
            
    end_time = time.time()
    log("on_query_completion time: " + str(end_time-start_time))
    log("number of completions: " + str(len(comps)))
    return comps

# EventListener are created once by sublime at start
class HaxeComplete( sublime_plugin.EventListener ):

    def on_load( self, view ) :

        if view is not None and view.file_name() is not None and ViewTools.is_unsupported(view): 
            hxproject.currentProject(view).generate_build( view )


    def on_post_save( self , view ) :
        if ViewTools.is_hxml(view):
            project = hxproject.currentProject(view)
            project.clear_build()
            

    # if view is None it's a preview
    def on_activated( self , view ) :
        if view is not None and view.file_name() is not None and ViewTools.is_unsupported(view): 
            project = hxproject.currentProject(view)
            project.get_build(view)
            project.extract_build_args( view )
            project.generate_build(view)    


    def on_pre_save( self , view ) :

        if ViewTools.is_haxe(view) :
            ViewTools.create_missing_folders(view)


    def on_query_completions(self, view, prefix, locations):
        log("on_query_completions triggered")
        project = hxproject.currentProject(view)
        return auto_complete(project, view, prefix, locations)
        
    
    

    # def on_modified( self , view ):
    #   print "on_modified"
    #   win = sublime.active_window()
    #   if win is None :
    #       return None

    #   isOk = ( win.active_view().buffer_id() == view.buffer_id() )
    #   if not isOk :
    #       return None
        
    #   sel = view.sel()
    #   caret = 0
    #   for s in sel :
    #       caret = s.a
        
    #   if caret == 0 or not CaretTools.in_haxe_code(view, caret):
    #       return None

    #   src = view.substr(sublime.Region(0, view.size()))
    #   ch = src[caret-1]
    #   #print(ch)
    #   if ch not in ".(:, " :
    #       #print("here")
    #       print "on modified run completion"
    #       view.run_command("haxe_display_completion")
    #   #else :
    #   #   view.run_command("haxe_insert_completion")



    #def run_build( self , view ) :
    #   print "run build"
    #   err, comps, status = self.get_compiler_completion( view )
    #   view.set_status( "haxe-status" , status )
    #   panel().status( "haxe-status" , status )
    #   print status


#sublime.set_timeout(HaxeLib.scan, 200)