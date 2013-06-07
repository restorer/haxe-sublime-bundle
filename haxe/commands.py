import sublime, sublime_plugin
import os
import re
import json
import codecs
import functools

from sublime import Region


is_st3 = int(sublime.version()) >= 3000

if is_st3:
    import Haxe.haxe.tools.view as view_tools
    import Haxe.haxe.project as hxproject
    import Haxe.haxe.codegen as hxcodegen
    import Haxe.haxe.tools.path as path_tools
    import Haxe.haxe.hxtools as hxsrctools
    import Haxe.haxe.settings as hxsettings
    import Haxe.haxe.completion.hx.constants as hxcc

    import Haxe.haxe.tools.view as view_tools
    import Haxe.haxe.temp as hxtemp

    from Haxe.haxe.log import log
    from Haxe.haxe.completion.hx.types import CompletionOptions
    from Haxe.haxe.completion.hx.base import trigger_completion
else:
    import haxe.tools.view as view_tools
    import haxe.project as hxproject
    import haxe.codegen as hxcodegen
    import haxe.tools.path as path_tools
    import haxe.hxtools as hxsrctools
    import haxe.settings as hxsettings
    import haxe.completion.hx.constants as hxcc
    import haxe.tools.view as view_tools
    import haxe.temp as hxtemp

    from haxe.log import log
    from haxe.completion.hx.types import CompletionOptions
    from haxe.completion.hx.base import trigger_completion

plugin_path = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))



word_chars = re.compile("[a-z0-9_]", re.I)

class HaxeFindDeclarationCommand( sublime_plugin.TextCommand ):
    def run( self , edit ) :
        self.run1(True, False)

    def run1 (self, use_display, inline_workaround = False):
        print("run HaxeFindDeclarationCommand")
        view = self.view

        file_name = view.file_name()

        if file_name == None:
            return

        project = hxproject.current_project(view)
        build = project.get_build(view).copy()
        build.args.append(("-D", "no-inline"))
        log("ARGS:" + str(build.args))
        log("ARGS2" + str(project.get_build(view).args))
        src = view_tools.get_content(view)

        file_name = os.path.basename(view.file_name())

        using_line = "\nusing hxsublime.FindDeclaration;\n"

        pos = view.sel()[0].a

        word = view.word(pos)

        word_start = word.a
        word_end = word.b

        word_str = src[word_start:word_end]

        prev = src[word_start-1]
        
        field_access = False
        if prev == ".":
            field_access = True

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
        else:
            new_src = new_src[0:package_decl.end(0)]+using_line+new_src[package_decl.end(0):len(new_src)]

        temp_path, temp_file = hxtemp.create_temp_path_and_file(build, view.file_name(), new_src)

        build.add_classpath(temp_path)

        build.add_classpath(os.path.join(plugin_path, "haxetools"))
        
        if use_display:
            build.set_auto_completion(temp_file + "@0", False)

        server_mode = project.is_server_mode()


        out, err = build.run_sync(project, view )

        hxtemp.remove_path(temp_path)
        

        file_pos = re.compile("\|\|\|\|\|([^|]+)\|\|\|\|\|", re.I)

        res = re.search(file_pos, out)
        if res != None:
            #we've got a proper response
            json_str = res.group(1)
            json_res = json.loads(json_str)

            self.handle_json_response(json_res, add, using_line, word_end, build, temp_path, temp_file, use_display, inline_workaround)
        else:

            if use_display:
                log("nothing found yet (2), try again without display (workaround)")
                self.run1(False)
            else:
                log("nothing found (3), cannot find declaration")

    def handle_json_response(self, json_res, add, using_line, word_end, build, temp_path, temp_file, use_display, inline_workaround):
        view = self.view
        if "file" in json_res:
            file = json_res["file"]
            min = json_res["min"]
            max = json_res["max"]

            #abs_path = abs_path.replace(build.get_relative_path(temp_file), build.get_relative_path(view.file_name())
            
            abs_path = path_tools.join_norm(build.get_build_folder(), file)
            abs_path_temp = path_tools.join_norm(build.get_build_folder(), build.get_relative_path(os.path.join(temp_path, temp_file)))


            if (abs_path == temp_file):
                if min > word_end:
                    min -= len(add)
                min -= len(using_line)
                # we have manually stored a temp file with only \n line endings
                # so we don't have to adjust the real file position and the sublime
                # text position
            else:
                f = codecs.open(abs_path, "r", "utf-8")
                real_source = f.read()
                f.close()
                # line endings could be \r\n, but sublime text has only \n after
                # opening a file, so we have to calculate the offset betweet the
                # returned position and the real position by counting all \r before min
                # should be moved to a utility function
                offset = 0
                for i in range(0,min):
                    
                    if real_source[i] == u"\r":
                        offset += 1
                log("offset: " + str(offset))

                min -= offset

            if (abs_path == temp_file):
                # file is active view
                abs_path = view.file_name()
                target_view = view
   

                log("line ending: " + str(view.settings().get("line_ending")))

                target_view.sel().clear()
                target_view.sel().add(sublime.Region(min))

                target_view.show(sublime.Region(min))
            else:
                global find_decl_pos, find_decl_file
                find_decl_file = abs_path
                find_decl_pos = min
                # open file and listen => HaxeFindDeclarationListener
                target_view = view.window().open_file(abs_path)

        elif "error" in json_res:
            error = json_res["error"]
            if (error =="inlined" and not inline_workaround):
                # try workaround when the current method was inlined (extern inlines are forced) by the compiler
                self.run1(use_display, True)
            else:
                log("nothing found (1), cannot find declaration")
        else:
            # can we really get here??????
            if use_display:
                log("nothing found yet (1), try again without display (takes longer, workaround for a compiler bug)")
                self.run1(False)
            else:
                log("nothing found (2), cannot find declaration")

#shared between FindDelaration Command and Listener
find_decl_file = None
find_decl_pos = None

class HaxeFindDeclarationListener(sublime_plugin.EventListener):

    def on_activated(self, view):
        global find_decl_pos, find_decl_file


        min = find_decl_pos

        if (view != None and view.file_name() != None):
            if (view.file_name() == find_decl_file):

                view.sel().clear()

                view.sel().add(sublime.Region(min))
                # move to line is delayed, seems to work better
                # without delay the animation to the region does not work properly sometimes
                def show ():
                    view.show_at_center(sublime.Region(min))
                sublime.set_timeout(show, 70)
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


class HaxeAsyncTriggeredCompletionCommand( sublime_plugin.TextCommand ):
    def run( self , edit) :

        options = CompletionOptions(
            hxcc.COMPLETION_TRIGGER_ASYNC, 
            hxcc.COMPILER_CONTEXT_REGULAR, 
            hxcc.COMPLETION_TYPE_REGULAR)
        trigger_completion(self.view, options)


class HaxeDisplayCompletionCommand( sublime_plugin.TextCommand ):
    def run( self , edit, input_char = None) :
        log("RUN - HaxeDisplayCompletionCommand")
        if input_char != None:
            self.view.run_command("insert" , {
                "characters" : input_char
            })
        log("RUN - HaxeDisplayCompletionCommand")
        options = CompletionOptions(
            hxcc.COMPLETION_TRIGGER_MANUAL, 
            hxcc.COMPILER_CONTEXT_REGULAR, 
            hxcc.COMPLETION_TYPE_REGULAR)
        trigger_completion(self.view, options)


class HaxeDisplayMacroCompletionCommand( sublime_plugin.TextCommand ):
    def run( self , edit ) :
        log("RUN - HaxeDisplayMacroCompletionCommand")
        options = CompletionOptions(
            hxcc.COMPLETION_TRIGGER_MANUAL, 
            hxcc.COMPILER_CONTEXT_REGULAR, 
            hxcc.COMPLETION_TYPE_REGULAR)
        trigger_completion(self.view, options)
        
        

class HaxeHintDisplayCompletionCommand( sublime_plugin.TextCommand ):
    def run( self , edit ) :
        log("RUN - HaxeHintDisplayCompletionCommand")
        options = CompletionOptions(
            hxcc.COMPLETION_TRIGGER_MANUAL, 
            hxcc.COMPILER_CONTEXT_REGULAR, 
            hxcc.COMPLETION_TYPE_HINT)
        trigger_completion(self.view, options)

class HaxeMacroHintDisplayCompletionCommand( sublime_plugin.TextCommand ):
    def run( self , edit ) :
        log("RUN - HaxeMacroHintDisplayCompletionCommand")
        options = CompletionOptions(
            hxcc.COMPLETION_TRIGGER_MANUAL, 
            hxcc.COMPILER_CONTEXT_MACRO, 
            hxcc.COMPLETION_TYPE_HINT)
        trigger_completion(self.view, options)
        



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

class HaxeRunBuildAltCommand( sublime_plugin.TextCommand ):
    def run( self , edit ) :
        view = self.view
        log("run HaxeRunBuildCommand")
        project = hxproject.current_project(self.view)

        if len(project.builds) == 0:
            log("no builds available")
            project.extract_build_args(view, True);
        else:
            project.run_build( view )

class HaxeSelectBuildCommand( sublime_plugin.TextCommand ):
    def run( self , edit ) :
        log("run HaxeSelectBuildCommand")
        view = self.view
        
        hxproject.current_project(self.view).select_build( view )

# called 

class HaxeRestartServerCommand( sublime_plugin.WindowCommand ):

    def run( self ) : 
        log("run HaxeRestartServerCommand")
        view = sublime.active_window().active_view()
        
        project = hxproject.current_project(view)

        project.server.stop(lambda: project.start_server( view ) )
        



class HaxeGenerateUsingCommand( sublime_plugin.TextCommand ):
    def run( self , edit ) :
        log("run HaxeGenerateUsingCommand")
        hxcodegen.generate_using(self.view, edit)
        

class HaxeGenerateImportCommand( sublime_plugin.TextCommand ):

    def run( self, edit ) :
        log("run HaxeGenerateImportCommand")
        hxcodegen.generate_import(self.view, edit)
        


# stores the info for file creation, is shared between the command and listener instances.
current_create_type_info = {}

# TODO Cleanup HaxeCreateTypeCommand

class HaxeCreateTypeCommand( sublime_plugin.WindowCommand ):

    
    

    def __init__ (self, win):
        
        self.classpath = None
        self.win = win


    def run( self , paths = [] , t = "class" ) :
        log("createtype")
        
        win = self.win      
        view = win.active_view()

        project = hxproject.current_project(view)

        builds = list(project.builds)

        if project.has_build():
            builds.insert(0, project.get_build(view))

        

        #scopes = view.scope_name(view.sel()[0].end()).split()
        
        pack = [];

        
        
        if len(builds) == 0 and view != None and view.file_name() != None:
            print(view.file_name())
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
                log("build file: " + b.build_file)
                found = False
                for cp in b.classpaths :
                    log("class path: " + cp)
                    log("path: " + path)
                    if path.startswith( cp ) :
                        
                        self.classpath = path[0:len(cp)]
                        log("self.classpath: " + self.classpath)
                        
                        rel_path = path[len(cp):]
                        
                        if len(rel_path) == 0:
                            found = True
                        else:
                            sub_packs = rel_path.split(os.sep)
                            log("subpacks:" + str(sub_packs))
                            for p in sub_packs :
                                if "." in p : 
                                    break
                                elif p :
                                    pack.append(p)
                                   
                                    found = True
     
                    if found:
                        break
                if found:
                    break
                log("found: " + str(found))



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
                        project.check_sublime_build( view )
                    else:
                        project.extract_build_args(view, False)
                        build = project.get_build(view)
                        if (build != None):
                            project.check_sublime_build( view )



class HaxeCreateTypeListener( sublime_plugin.EventListener ):

    def on_load (self, view):
        can_create_file = view is not None and view.file_name() != None and view.file_name() in current_create_type_info and view.size() == 0
        
        if can_create_file:
            self.create_file(view)




    def create_file(self, view):
        
        data = current_create_type_info[view.file_name()];
        
        def run_edit(v, edit):
            v.insert(edit,0,data)
            v.end_edit(edit)
            sel = v.sel()
            sel.clear()
            pt = v.text_point(5,1)
            sel.add( sublime.Region(pt,pt) )

        view_tools.async_edit(view, run_edit)
         




class HaxeInstallLibCommand( sublime_plugin.WindowCommand ):

    def run(self):

        view = sublime.active_window().active_view()

        project = hxproject.current_project(view)

        if project is not None:
            manager = project.haxelib_manager
            libs = manager.search_libs()
            menu = self._prepare_menu(libs, manager)
            on_selected = functools.partial(self._entry_selected, libs, manager)
            self.window.show_quick_panel(menu, on_selected)

    def _prepare_menu (self, libs, manager):
        menu = []
        for l in libs :
            if manager.is_lib_installed(l):
                menu.append( [ l + " [" + manager.get_lib(l).version + "]" , "Remove" ] )
            else :
                menu.append( [ l , 'Install' ] )

        menu.append( ["Upgrade libraries", "Upgrade installed libraries"] )
        menu.append( ["Haxelib Selfupdate", "Updates Haxelib itself"] )
        
        return menu

    def _entry_selected( self, libs, manager, i ):

        if i < 0 :
            return
        if i == len(libs) :
            manager.upgrade_all()
            
        if i == len(libs)+1 :
            manager.self_update()
        else :
            lib = libs[i]
            if lib in manager.available :
                manager.remove_lib(lib)
            else :
                manager.install_lib(lib)



############# Copy of Default exec.py with some modifications ##########

import sublime, sublime_plugin
import os, sys
if is_st3:
    import _thread as thread
else:
    import thread
import subprocess
import functools
import time


class ProcessListener(object):
    def on_data(self, proc, data):
        pass

    def on_finished(self, proc):
        pass


try :
    stexec = __import__("exec")
    ExecCommand = stexec.ExecCommand
    AsyncProcess = stexec.AsyncProcess 
except ImportError as e :
    import Default
    stexec = getattr( Default , "exec" )
    ExecCommand = stexec.ExecCommand
    AsyncProcess = stexec.AsyncProcess
    
       
class HaxeExecCommand(sublime_plugin.WindowCommand, ProcessListener):
    def run(self, cmd = [], file_regex = "", line_regex = "", working_dir = "",
            encoding = None, env = {}, quiet = False, kill = False, is_check_run = False,
            # Catches "path" and "shell"
            **kwargs):

        print("ENV1: " + str(env))

        self.is_check_run = is_check_run;

        if encoding is None :
            if is_st3 :
                encoding = sys.getfilesystemencoding()
            else:
                encoding = "utf-8"

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
        
        log("WORKING DIR:" + working_dir)
        # Call get_output_panel a second time after assigning the above
        # settings, so that it'll be picked up as a result buffer
        self.window.get_output_panel("exec")

        self.encoding = encoding
        self.quiet = quiet

        self.proc = None
        if not self.quiet:
            print("Running Command : " + " ".join(cmd))

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
            if is_st3:
                print("CMD:" + str(cmd))
                print("ENV:" + str(merged_env))
                self.proc = AsyncProcess(cmd, None, merged_env, self, **kwargs)
            else:
                self.proc = AsyncProcess(cmd, merged_env, self, **kwargs)

            self.append_data(self.proc, "Running Command: " + " ".join(cmd) + "\n")
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
                try:
                    proc.kill()
                except:
                    pass
            return

        try:
            if not is_st3 or isinstance(data, bytes):
                st = data.decode(self.encoding)
            else:
                st = data
                    
        except:
            st = "[Decode error - output not " + self.encoding + "]\n"
            proc = None

        # quick and dirty workaround, nme and openfl display errors when --no-output is defined, 
        # maybe we should move to normal haxe/hxml run with --no-output, this way we can also use server_mode caching
        if self.is_check_run and st.find("Embedding assets failed! We encountered an error accessing") > -1:
            return

        # Normalize newlines, Sublime Text always uses a single \n separator
        # in memory.
        st = st.replace('\r\n', '\n').replace('\r', '\n')

        selection_was_at_end = (len(self.output_view.sel()) == 1
            and self.output_view.sel()[0]
                == sublime.Region(self.output_view.size()))
        
        
        def do_edit(v, edit):

            v.set_read_only(False)
            
            v.insert(edit, self.output_view.size(), st)
            if selection_was_at_end:
                v.show(self.output_view.size())
            v.end_edit(edit)

            v.set_read_only(True)
            
        view_tools.async_edit(self.output_view, do_edit)

    def finish(self, proc):
        
        v = self.output_view
        
        if not self.quiet:
            elapsed = time.time() - proc.start_time
            exit_code = proc.exit_code()
            
            
            if exit_code == 0 or exit_code == None:
                self.append_data(proc, ("[Finished in %.1fs]") % (elapsed))
            else:
                self.append_data(proc, ("[Finished in %.1fs with exit code %d]") % (elapsed, exit_code))
        
        if proc != self.proc:
            return

        # Set the selection to the start, so that next_result will work as expected
        
        v.sel().clear()
        v.sel().add(sublime.Region(0))
        

    def on_data(self, proc, data):
        
        sublime.set_timeout(lambda : log(data), 0)
        sublime.set_timeout(functools.partial(self.append_data, proc, data), 0)

    def on_finished(self, proc):
        sublime.set_timeout(functools.partial(self.finish, proc), 0)



