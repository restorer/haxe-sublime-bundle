import sys
#sys.path.append("/usr/lib/python2.6/")
#sys.path.append("/usr/lib/python2.6/lib-dynload")



#sys.path.append("/usr/lib/python2.6/")
#sys.path.append("/usr/lib/python2.6/lib-dynload")

import sublime

import os


#import xml.parsers.expat

import haxe.haxe_complete 

import haxe.haxe_lib

import haxe.haxe_panel

haxe_lib = sys.modules["haxe.haxe_lib"]
haxe_panel = sys.modules["haxe.haxe_panel"]


from startup import STARTUP_INFO

from subprocess import Popen, PIPE

import haxe.haxe_settings

stexec = __import__("exec") 




def runcmd( args, input=None ):
	#print(args)

	settings = haxe.haxe_settings.HaxeSettings
	cwd = "."
	try: 
		libPath = settings.haxeLibraryPath();
		
		env = os.environ.copy()
		if libPath != None :
			#print "std lib: set: " + libPath
			#env = {}
			print "export HAXE_LIBRARY_PATH="+libPath
			env["HAXE_LIBRARY_PATH"] = libPath 
		args = filter(lambda s: s != "", args)
		
		
		#print sys.getfilesystemencoding()
		#p = Popen(,  stdout=PIPE, stderr=PIPE, stdin=PIPE, startupinfo=STARTUP_INFO, env=env)

		encodedArgs = [a.encode(sys.getfilesystemencoding()) for a in args]
		print " ".join(encodedArgs)
		p = Popen(encodedArgs, cwd=cwd, stdout=PIPE, stderr=PIPE, stdin=PIPE, startupinfo=STARTUP_INFO, env=env)
		


		if isinstance(input, unicode):
			input = input.encode('utf-8')
		out, err = p.communicate(input=input)
		print "output: " + out.decode('utf-8')
		
		#print "error: " + err
		return (out.decode('utf-8') if out else '', err.decode('utf-8') if err else '')
	except (OSError, ValueError) as e:
		err = u'Error while running %s: in %s (%s)' % (args[0], cwd, e)
		return ("", err.decode('utf-8'))

class HaxeExecCommand(stexec.ExecCommand):
	def finish(self, *args, **kwargs):
		super(HaxeExecCommand, self).finish(*args, **kwargs)  
		outp = self.output_view.substr(sublime.Region(0, self.output_view.size()))
		hc = haxe.haxe_complete.HaxeComplete.instance()
		hc.errors = hc.extract_errors( outp )
		hc.highlight_errors( self.window.active_view() )

	def run(self, cmd = [], file_regex = "", line_regex = "", working_dir = "",
			encoding = "utf-8", env = {}, quiet = False, kill = False,
			# Catches "path" and "shell"
			**kwargs):

		if kill:
			if self.proc:
				self.proc.kill()
				self.proc = None
				self.append_data(None, "[Cancelled]")
			return

		if not hasattr(self, 'output_view'):
			# Try not to call get_output_panel until the regexes are assigned
			self.output_view = self.window.get_output_panel("exec")

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
			print "Running " + " ".join(cmd).encode('utf-8')
			haxe_panel.HaxePanel.writeln("Building")
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
			self.proc = stexec.AsyncProcess(cmd, merged_env, self, **kwargs)
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





class HaxelibExecCommand(stexec.ExecCommand):

	def run(self, *args, **kwargs):

		print "hello running"
		super(HaxelibExecCommand, self).run(*args, **kwargs)

	def finish(self, *args, **kwargs):
		super(HaxelibExecCommand, self).finish(*args, **kwargs)  
		print "haxelibExec"
		haxe_lib.HaxeLib.scan()



