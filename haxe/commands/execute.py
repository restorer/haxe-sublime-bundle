import sublime, sublime_plugin
import os,sys

import functools
import time

from haxe.plugin import is_st3
from haxe.tools import viewtools
from haxe.log import log

from haxe.tools.stringtools import encode_utf8, to_unicode

if is_st3:
    import _thread as thread
else:
    import thread

try :
    stexec = __import__("exec")
    ExecCommand = stexec.ExecCommand
    AsyncProcess = stexec.AsyncProcess 
except ImportError as e :
    import Default
    stexec = getattr( Default , "exec" )
    ExecCommand = stexec.ExecCommand
    AsyncProcess = stexec.AsyncProcess


class ProcessListener(object):
    def on_data(self, proc, data):
        pass

    def on_finished(self, proc):
        pass


def _escape_cmd(cmd):
    print_cmd = list(cmd)
    l = len(print_cmd)
    for i in range(0, l):
        e = print_cmd[i]
        if e == "--macro" and i < l-1:
            print_cmd[i+1] = "'" + print_cmd[i+1] + "'"
    return print_cmd

class HaxeExecCommand(sublime_plugin.WindowCommand, ProcessListener):
    def run(self, cmd = [], file_regex = "", line_regex = "", working_dir = "",
            encoding = None, env = {}, quiet = False, kill = False, is_check_run = False,
            # Catches "path" and "shell"
            **kwargs):

        log("ENV1: " + str(env))

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
            
            def escape_arg(a):
                a = '\\"'.join(a.split('"'))
                if len(a) >= 2:
                    a = '"' + a[2:] if a.startswith('\\"') else a
                    a = a[0:len(a)-2] + '"' if a.endswith('\\"') else a
                return encode_utf8(a)                


            log("Running Command : " + " ".join(map(escape_arg, cmd)))

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
                log("CMD:" + str(cmd))
                log("ENV:" + str(merged_env))
                self.proc = AsyncProcess(cmd, None, merged_env, self, **kwargs)
            else:
                self.proc = AsyncProcess(cmd, merged_env, self, **kwargs)

            self.append_data(self.proc, "Running Command: " + " ".join(_escape_cmd(cmd)) + "\n")
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
            st = encode_utf8(data)
            
                    
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
            
        viewtools.async_edit(self.output_view, do_edit)

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



