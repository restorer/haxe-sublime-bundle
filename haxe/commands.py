import sublime, sublime_plugin
import os
import re
import json
from sublime import Region

import haxe.project as hxproject
import haxe.codegen
import haxe.tools.path as path_tools
import haxe.hxtools as hxsrctools
import haxe.settings as hxsettings
from haxe.log import log

import haxe.tools.view as view_tools
import haxe.temp as hxtemp

plugin_path = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

#class HaxelibExecCommand(stexec.ExecCommand):
#
#   def run(self, *args, **kwargs):
#
#       print "hello running"
#       super(HaxelibExecCommand, self).run(*args, **kwargs)
#
#   def finish(self, *args, **kwargs):
#       super(HaxelibExecCommand, self).finish(*args, **kwargs)  
#       print "haxelibExec"
#       hxlib.HaxeLib.scan()

word_chars = re.compile("[a-z0-9_]", re.I)

class HaxeFindDeclarationCommand( sublime_plugin.TextCommand ):
    def run( self , edit ) :
        self.run1(True, False)

    def run1 (self, use_display, inline_workaround = False):
        print "HaxeFindDeclarationCommand"
        view = self.view

        file_name = view.file_name()

        if file_name == None:
            return

        project = hxproject.current_project(view)
        build = project.get_build(view).copy()
        build.args.append(("-D", "no-inline"))

        src = view_tools.get_content(view)

        file_name = os.path.basename(view.file_name())

        

        using_line = "\nusing hxsublime.FindDeclaration;\n"

        pos = view.sel()[0].a

        word = view.word(pos)

        word_start = word.a
        word_end = word.b

        log(src[word_end:len(src)])
        
        word_str = src[word_start:word_end]
        log(word_str)

        

        

        prev = src[word_start-1]

        
        field_access = False
        if prev == ".":
            field_access = True

        log(field_access)


        log(pos)
        log(word)
        add = ".sublime_find_decl()"

        if use_display:
            add += ".|"

        start = src[0:word_start]

        end = src[word_end:]

        if inline_workaround:
            add_x = "sublime_find_decl"         
            add_y = ""
            if use_display:
                add_y = ".|"
            new_src = start + add_x + "(" + word_str + ")" + add_y + end;
        else:
            new_src = start + word_str + add + end;

        package_decl = re.search(hxsrctools.package_line, new_src)

        if (package_decl == None):
            new_src = using_line + new_src
            log("new_src: " + new_src)
        else:
            new_src = new_src[0:package_decl.end(0)]+using_line+new_src[package_decl.end(0):len(new_src)]
            log("new_src: " + new_src)

        temp_path, temp_file = hxtemp.create_temp_path_and_file(build, view.file_name(), new_src)

        log("here we go")
        build.add_classpath(temp_path)

        
        log("plugin_path: " + plugin_path);
        build.add_classpath(plugin_path)
        
        if use_display:
            build.set_auto_completion(temp_file + "@0", False, False)

        server_mode = project.is_server_mode()

        log("run")
        out, err = build.run(project.haxe_exec(), project.haxe_env(), server_mode, view, project)
        log("run complete")
        hxtemp.remove_path(temp_path)
        

        file_pos = re.compile("\|\|\|\|\|([^|]+)\|\|\|\|\|", re.I)

        res = re.search(file_pos, out)
        if res != None:

            log("found position")

            

            json_str = res.group(1)

            json_res = json.loads(json_str)

            log(json_res)

            if "file" in json_res:
                file = json_res["file"]
                min = json_res["min"]
                max = json_res["max"]

                




                log(file)
                log(min)
                log(max)



                #abs_path = abs_path.replace(build.get_relative_path(temp_file), build.get_relative_path(view.file_name())
                
                log("temp_path: " + temp_path)
                log("temp_file: " + temp_file)
                abs_path = path_tools.join_norm(build.get_build_folder(), file)
                abs_path_temp = path_tools.join_norm(build.get_build_folder(), build.get_relative_path(os.path.join(temp_path, temp_file)))

                log("build_rel: " + build.get_relative_path(os.path.join(temp_path, temp_file)))
                log("abs_path: " + abs_path)
                log("abs_path_temp: " + abs_path_temp)

                

                if (abs_path == temp_file):
                    
                    abs_path = view.file_name()
                    target_view = view
                    m = min
                    log("word_end: " + str(word_end))
                    log("min: " + str(min))
                    if min > word_end:
                        m -= len(add)
                    m -= len(using_line)
                    target_view.sel().clear()
                    target_view.sel().add(sublime.Region(m))
                    target_view.show(sublime.Region(m))
                    #target_view.sel().clear()
                    #target_view.sel().add(sublime.Region(min))
                else:
                    global find_decl_pos, find_decl_file
                    find_decl_file = abs_path
                    find_decl_pos = min
                    target_view = view.window().open_file(abs_path)
                    

                


            elif "error" in json_res:
                error = json_res["error"]
                log(error)
                if (error =="inlined" and not inline_workaround):
                    self.run1(use_display, True)
                else:
                    log("nothing found, no chance")
            else:
                log("nothing found try again")
                if use_display:

                    self.run1(False)
                else:
                    log("nothing found, no chance")
        else:
            log("nothing found, try again")
            if use_display:
                self.run1(False)
            else:
                log("nothing found, no chance")


            
            

            #log(new_src.find_all(hxsrctools.type_decl))

            # remove temp path and file
            #


find_decl_file = None
find_decl_pos = None

class HaxeFindDeclarationListener(sublime_plugin.EventListener):

    def on_activated(self, view):
        log("on activated")
        global find_decl_pos, find_decl_file

        min = find_decl_pos

        if (view != None and view.file_name() != None):
            if (view.file_name() ==  find_decl_file):
                view.sel().clear()
                view.sel().add(sublime.Region(min))
                view.show_at_center(sublime.Region(min))
            find_decl_file = None
            find_decl_pos = None



class HaxeGetTypeOfExprCommand (sublime_plugin.TextCommand ):
    def run( self , edit ) :
        

        view = self.view
        
        file_name = view.file_name()

        if file_name == None:
            return

        file_name = os.path.basename(view.file_name())

        window = view.window()
        folders = window.folders()
 
        project_dir = folders[0]
        tmp_folder = folders[0] + "/tmp"
        target_file = folders[0] + "/tmp/" + file_name

        if os.path.exists(tmp_folder):
            path_tools.remove_dir(tmp_folder)           
        

        os.makedirs(tmp_folder)
        

        fd = open(target_file, "w+")
        sel = view.sel()

        word = view.substr(sel[0])

        replacement = "(hxsublime.Utils.getTypeOfExpr(" + word + "))."

        newSel = Region(sel[0].a, sel[0].a + len(replacement))


        view.replace(edit, sel[0], replacement)

        newSel = view.sel()[0]

        view.replace(edit, newSel, word)

        new_content = view.substr(sublime.Region(0, view.size()))
        fd.write(new_content)

        view.run_command("undo")


class HaxeDisplayCompletion( sublime_plugin.TextCommand ):

    def run( self , edit ) :

        log("run HaxeDisplayCompletion")
        
        view = self.view
        project = hxproject.current_project(view)
        project.completion_context.set_manual_trigger(view, False)
        

        self.view.run_command( "auto_complete" , {
            "api_completions_only" : True,
            "disable_auto_insert" : True,
            "next_completion_if_showing" : False,
            'auto_complete_commit_on_tab': True
        })


class HaxeDisplayMacroCompletion( sublime_plugin.TextCommand ):
    
    def run( self , edit ) :
        
        log("run HaxeDisplayMacroCompletion")
        
        view = self.view
        project = hxproject.current_project(view)
        project.completion_context.set_manual_trigger(view, True)
        
        
        view.run_command( "auto_complete" , {
            "api_completions_only" : True,
            "disable_auto_insert" : True,
            "next_completion_if_showing" : False,
            'auto_complete_commit_on_tab': True
        } )

        

class HaxeInsertCompletionCommand( sublime_plugin.TextCommand ):
    
    def run( self , edit ) :
        log("run HaxeInsertCompletion")
        view = self.view

        view.run_command( "insert_best_completion" , {
            "default" : ".",
            "exact" : True
        } )

class HaxeSaveAllAndBuildCommand( sublime_plugin.TextCommand ):
    def run( self , edit ) :
        log("run HaxeSaveAllAndBuildCommand")
        view = self.view
        view.window().run_command("save_all")
        hxproject.current_project(self.view).run_sublime_build( view )

class HaxeRunBuildCommand( sublime_plugin.TextCommand ):
    def run( self , edit ) :
        view = self.view
        log("run HaxeRunBuildCommand")
        project = hxproject.current_project(self.view)

        if len(project.builds) == 0:
            log("no builds available")
            project.extract_build_args(view, True);
        else:
            project.run_sublime_build( view )


class HaxeSelectBuildCommand( sublime_plugin.TextCommand ):
    def run( self , edit ) :
        log("run HaxeSelectBuildCommand")
        view = self.view
        
        hxproject.current_project(self.view).select_build( view )

# called 
class HaxeHintCommand( sublime_plugin.TextCommand ):
    def run( self , edit ) :
        log("run HaxeHintCommand")
        
        view = self.view
        
        view.run_command('auto_complete', {'disable_auto_insert': True})
        


class HaxeRestartServerCommand( sublime_plugin.WindowCommand ):

    def run( self ) : 
        log("run HaxeRestartServerCommand")
        view = sublime.active_window().active_view()
        
        project = hxproject.current_project(view)

        project.server.stop()
        project.start_server( view )



class HaxeGenerateUsingCommand( sublime_plugin.TextCommand ):
    def run( self , edit ) :
        log("run HaxeGenerateUsingCommand")
        haxe.codegen.generate_using(self.view, edit)
        

class HaxeGenerateImportCommand( sublime_plugin.TextCommand ):

    def run( self, edit ) :
        log("run HaxeGenerateImportCommand")
        
        haxe.codegen.generate_import(self.view, edit)
        


# stores the info for file creation, is shared between the command and listener instances.
current_create_type_info = {}

class HaxeCreateTypeCommand( sublime_plugin.WindowCommand ):

    
    

    def __init__ (self, win):
        
        self.classpath = None
        self.win = win


    def run( self , paths = [] , t = "class" ) :
        log("createtype")
        
        win = self.win      
        view = win.active_view()

        project = hxproject.current_project(view)

        builds = project.builds

        #scopes = view.scope_name(view.sel()[0].end()).split()
        
        pack = [];

        if len(builds) == 0 and view != None and view.file_name() != None:
            print view.file_name()
            project.extract_build_args(view)
            builds = project.builds

        if len(paths) == 0 and view != None:
            fn = view.file_name()
            paths.append(fn)

        for path in paths :

            if os.path.isfile( path ) :
                path = os.path.dirname( path )

            if self.classpath is None :
                self.classpath = path

            for b in builds :
                found = False
                for cp in b.classpaths :


                    if path.startswith( cp ) :
                        
                        self.classpath = path[0:len(cp)]
                        for p in path[len(cp):].split(os.sep) :
                            if "." in p : 
                                break
                            elif p :
                                pack.append(p)
                               
                                found = True
                        if found:
                            break
                    if found:
                        break
                if found:
                    break


        if self.classpath is None :
            if len(builds) > 0 :
                self.classpath = builds[0].classpaths[0]

        # so default text ends with .
        if len(pack) > 0 :
            pack.append("")
                        
        
        sublime.status_message( "Current classpath : " + self.classpath )
        win.show_input_panel("Enter "+t+" name : " , ".".join(pack) , lambda inp: self.on_done(inp, t) , self.on_change , self.on_cancel )

    def on_done( self , inp, cur_type ) :

        fn = self.classpath;
        parts = inp.split(".")
        pack = []

        while( len(parts) > 0 ):
            p = parts.pop(0)
            
            fn = os.path.join( fn , p )
            if hxsrctools.is_type.match( p ) : 
                cl = p
                break;
            else :
                pack.append(p)

        if len(parts) > 0 :
            cl = parts[0]

        fn += ".hx"
        
        
        
        src = "\npackage " + ".".join(pack) + ";\n\n"+cur_type+" "+cl+" " 
        if cur_type == "typedef" :
            src += "= "
        src += "{\n\n\t\n\n}"

        current_create_type_info[fn] = src

        sublime.active_window().open_file( fn )
 

    def on_change( self , inp ) :
        #sublime.status_message( "Current classpath : " + self.classpath )
        log( inp )

    def on_cancel( self ) :
        None


class HaxeBuildOnSaveListener ( sublime_plugin.EventListener ):
    def on_post_save(self, view):
        log("on_post_save")
        if view is not None and view.file_name() is not None:
            if view_tools.is_supported(view) or view.file_name().endswith(".erazor.html"):
                if (hxsettings.build_on_save()):
                    project = hxproject.current_project(view)
                
                    if len(project.builds) > 0:
                        project.run_sublime_build( view )
                    else:
                        project.extract_build_args(view, False)
                        build = project.get_build(view)
                        if (build != None):
                            project.run_sublime_build( view )



class HaxeCreateTypeListener( sublime_plugin.EventListener ):


    def on_activated( self, view ) : 
        self.create_file(view)      

    def on_load (self, view):
        self.create_file(view)


    def create_file(self, view):
        if view is not None and view.file_name() != None and view.file_name() in current_create_type_info and view.size() == 0 :
            e = view.begin_edit()
            view.insert(e,0,current_create_type_info[view.file_name()])
            view.end_edit(e)
            sel = view.sel()
            sel.clear()
            pt = view.text_point(5,1)
            sel.add( sublime.Region(pt,pt) )



############# Copy of Default exec.py including a temporary fix for umlauts in AsyncProcess ##########

import sublime, sublime_plugin
import os, sys
import thread
import subprocess
import functools
import time


class ProcessListener(object):
    def on_data(self, proc, data):
        pass

    def on_finished(self, proc):
        pass

# Encapsulates subprocess.Popen, forwarding stdout to a supplied
# ProcessListener (on a separate thread)
class AsyncProcess(object):
    def __init__(self, arg_list, env, listener,
            # "path" is an option in build systems
            path="",
            # "shell" is an options in build systems
            shell=False):

        self.listener = listener
        self.killed = False

        self.start_time = time.time()

        # Hide the console window on Windows
        startupinfo = None
        if os.name == "nt":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        # Set temporary PATH to locate executable in arg_list
        if path:
            old_path = os.environ["PATH"]
            # The user decides in the build system whether he wants to append $PATH
            # or tuck it at the front: "$PATH;C:\\new\\path", "C:\\new\\path;$PATH"
            
            ##### Dirty FIX 1 for umlauts, please clean up
            try:
                val = unicode(path, "ISO-8859-1").encode(sys.getfilesystemencoding())
            except:
                val = path.encode(sys.getfilesystemencoding())
            os.environ["PATH"] = os.path.expandvars(val)
            #os.environ["PATH"] = path.encode(sys.getfilesystemencoding())
            ##### END FIX 1
        proc_env = os.environ.copy()
        proc_env.update(env)
        for k, v in proc_env.iteritems():
            ##### Dirty FIX 2, for umlauts please clean up
            try:
                val = unicode(v, "ISO-8859-1").encode(sys.getfilesystemencoding())
            except:
                val = v.encode(sys.getfilesystemencoding())
            proc_env[k] = os.path.expandvars(val)
            #proc_env[k] = os.path.expandvars(v).encode(sys.getfilesystemencoding())
            ##### END FIX 2
        self.proc = subprocess.Popen(arg_list, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, startupinfo=startupinfo, env=proc_env, shell=shell)

        if path:
            os.environ["PATH"] = old_path

        if self.proc.stdout:
            thread.start_new_thread(self.read_stdout, ())

        if self.proc.stderr:
            thread.start_new_thread(self.read_stderr, ())

    def kill(self):
        if not self.killed:
            self.killed = True
            try:
                self.proc.terminate()
            except:
                pass
            self.listener = None

    def poll(self):
        return self.proc.poll() == None

    def exit_code(self):
        return self.proc.poll()

    def read_stdout(self):
        while True:
            data = os.read(self.proc.stdout.fileno(), 2**15)

            if data != "":
                if self.listener:
                    self.listener.on_data(self, data)
            else:
                self.proc.stdout.close()
                if self.listener:
                    self.listener.on_finished(self)
                break

    def read_stderr(self):
        while True:
            data = os.read(self.proc.stderr.fileno(), 2**15)

            if data != "":
                if self.listener:
                    self.listener.on_data(self, data)
            else:
                self.proc.stderr.close()
                break



class HaxeExecCommand(sublime_plugin.WindowCommand, ProcessListener):
    def run(self, cmd = [], file_regex = "", line_regex = "", working_dir = "",
            encoding = "utf-8", env = {}, quiet = False, kill = False,
            # Catches "path" and "shell"
            **kwargs):

        log("run haxe exec")
        if kill:
            if self.proc:
                self.proc.kill()
                self.proc = None
                self.append_data(None, "[Cancelled]")
            return

        if not hasattr(self, 'output_view'):
            # Try not to call get_output_panel until the regexes are assigned
            self.output_view = self.window.get_output_panel("exec")
            self.output_view.settings().set('word_wrap', True)

        # Default the to the current files directory if no working directory was given
        if (working_dir == "" and self.window.active_view()
                        and self.window.active_view().file_name()):
            working_dir = os.path.dirname(self.window.active_view().file_name())



        self.output_view.settings().set("result_file_regex", file_regex)
        self.output_view.settings().set("result_line_regex", line_regex)
        self.output_view.settings().set("result_base_dir", working_dir)
        

        # Call get_output_panel a second time after assigning the above
        # settings, so that it'll be picked up as a result buffer
        self.window.get_output_panel("exec")

        self.encoding = encoding
        self.quiet = quiet

        self.proc = None
        if not self.quiet:
            print "Running " + " ".join(cmd)

            sublime.status_message("Building")


        show_panel_on_build = sublime.load_settings("Preferences.sublime-settings").get("show_panel_on_build", True)
        if show_panel_on_build:
            self.window.run_command("show_panel", {"panel": "output.exec"})


        merged_env = env.copy()
        if self.window.active_view():
            user_env = self.window.active_view().settings().get('build_env')
            if user_env:
                merged_env.update(user_env)

        # Change to the working dir, rather than spawning the process with it,
        # so that emitted working dir relative path names make sense
        if working_dir != "":
            os.chdir(working_dir)

        err_type = OSError
        if os.name == "nt":
            err_type = WindowsError

        try:
            # Forward kwargs to AsyncProcess
            
            self.proc = AsyncProcess(cmd, merged_env, self, **kwargs)
            self.append_data(self.proc, "Running " + " ".join(cmd) + "\n")
        except err_type as e:
            self.append_data(None, str(e) + "\n")
            self.append_data(None, "[cmd:  " + str(cmd) + "]\n")
            self.append_data(None, "[dir:  " + str(os.getcwdu()) + "]\n")
            if "PATH" in merged_env:
                self.append_data(None, "[path: " + str(merged_env["PATH"]) + "]\n")
            else:
                self.append_data(None, "[path: " + str(os.environ["PATH"]) + "]\n")
            if not self.quiet:
                self.append_data(None, "[Finished]")

    def is_enabled(self, kill = False):
        if kill:
            return hasattr(self, 'proc') and self.proc and self.proc.poll()
        else:
            return True

    def append_data(self, proc, data):
        if proc != self.proc:
            # a second call to exec has been made before the first one
            # finished, ignore it instead of intermingling the output.
            if proc:
                proc.kill()
            return

        try:
            str = data.decode(self.encoding)
        except:
            str = "[Decode error - output not " + self.encoding + "]\n"
            proc = None

        # Normalize newlines, Sublime Text always uses a single \n separator
        # in memory.
        str = str.replace('\r\n', '\n').replace('\r', '\n')

        selection_was_at_end = (len(self.output_view.sel()) == 1
            and self.output_view.sel()[0]
                == sublime.Region(self.output_view.size()))
        self.output_view.set_read_only(False)
        edit = self.output_view.begin_edit()
        self.output_view.insert(edit, self.output_view.size(), str)
        if selection_was_at_end:
            self.output_view.show(self.output_view.size())
        self.output_view.end_edit(edit)
        self.output_view.set_read_only(True)

    def finish(self, proc):
        if not self.quiet:
            elapsed = time.time() - proc.start_time
            exit_code = proc.exit_code()
            
            
            if exit_code == 0 or exit_code == None:
                self.append_data(proc, ("[Finished in %.1fs]") % (elapsed))
            else:
                self.append_data(proc, ("[Finished in %.1fs with exit code %d]") % (elapsed, exit_code))

        if proc != self.proc:
            return

        errs = self.output_view.find_all_results()
        if len(errs) == 0:
            sublime.status_message("Build finished")
        else:
            sublime.status_message(("Build finished with %d errors") % len(errs))

        # Set the selection to the start, so that next_result will work as expected
        edit = self.output_view.begin_edit()
        self.output_view.sel().clear()
        self.output_view.sel().add(sublime.Region(0))
        self.output_view.end_edit(edit)

    def on_data(self, proc, data):
        sublime.set_timeout(lambda : log(data), 0)
        sublime.set_timeout(functools.partial(self.append_data, proc, data), 0)

    def on_finished(self, proc):
        sublime.set_timeout(functools.partial(self.finish, proc), 0)
