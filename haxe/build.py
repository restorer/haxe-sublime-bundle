import os
import re
import glob
import time
import codecs
import sublime

is_st3 = int(sublime.version()) >= 3000

if is_st3:
	import Haxe.haxe.config as hxconfig
	import Haxe.haxe.types as hxtypes
	import Haxe.haxe.lib as hxlib
	import Haxe.haxe.settings as hxsettings 
	import Haxe.haxe.tools.path as path_tools
	import Haxe.haxe.panel as hxpanel
	from Haxe.haxe.execute import run_cmd, run_cmd_async
	from Haxe.haxe.log import log
else:
	import haxe.config as hxconfig
	import haxe.types as hxtypes
	import haxe.lib as hxlib
	import haxe.settings as hxsettings 
	import haxe.tools.path as path_tools
	import haxe.panel as hxpanel
	from haxe.execute import run_cmd, run_cmd_async
	from haxe.log import log


hxml_cache = {}

# one hxml can contain multiple builds separated by --next
# should we really support this, or how can we handle this?
# should the user be able to select a part of the build for completion/build

def hxml_to_builds (build, folder):
	builds = []

	current_build = HaxeBuild()
	current_build.hxml = build
	build_path = os.path.dirname(build);

	# print("build file exists")
	f = codecs.open( build , "r+" , "utf-8" , "ignore" )
	while 1:
		l = f.readline() 
		if not l : 
			break;
		if l.startswith("--next") :
			builds.append( current_build )
			current_build = HaxeBuild()
			current_build.hxml = build
			
		l = l.strip()
		
		if l.startswith("-main") :
			spl = l.split(" ")
			if len( spl ) == 2 :
				current_build.main = spl[1]
			else :
				sublime.status_message( "Invalid build.hxml : no Main class" )
		
		if l.startswith("-lib") :
			spl = l.split(" ")
			if len( spl ) == 2 :
				lib = hxlib.HaxeLib.get( spl[1] )
				current_build.libs.append( lib )
			else :
				sublime.status_message( "Invalid build.hxml : lib not found" )

		if l.startswith("-cmd") :
			spl = l.split(" ")
			current_build.args.append( ( "-cmd" , " ".join(spl[1:]) ) )
		
		if l.startswith("--macro"):
			spl = l.split(" ")
			current_build.args.append( ( "--macro" , '"' +  "\"".join( " ".join(spl[1:]).split("\"")  ) + '"' ))	

		for flag in [ "lib" , "D" , "swf-version" , "swf-header", 
					"debug" , "-no-traces" , "-flash-use-stage" , "-gen-hx-classes" , 
					"-remap" , "-no-inline" , "-no-opt" , "-php-prefix" , 
					"-js-namespace" , "-interp" , "-dead-code-elimination" , 
					"-php-front" , "-php-lib", "dce" , "-js-modern", "-times" ] :
			if l.startswith( "-"+flag ) :
				current_build.args.append( tuple(l.split(" ") ) )
				
				break
		
		for flag in [ "resource" , "xml" , "x" , "swf-lib" ] :
			if l.startswith( "-"+flag ) :
				spl = l.split(" ")
				outp = os.path.join( folder , " ".join(spl[1:]) )
				current_build.args.append( ("-"+flag, outp) )
				if (flag == "x"):
					current_build.target = "neko"
				break

		for flag in hxconfig.targets:
			if l.startswith( "-" + flag + " " ) :
				spl = l.split(" ")
				#outp = os.path.join( folder , " ".join(spl[1:]) ) 
				outp = " ".join(spl[1:]) 
				current_build.args.append( ("-"+flag, outp) )
				
				current_build.target = flag
				current_build.output = outp
				break

		if l.startswith("-cp "):
			cp = l.split(" ")
			
			cp.pop(0)
			classpath = " ".join( cp )
			
			abs_classpath = path_tools.join_norm( build_path , classpath )
			current_build.classpaths.append( abs_classpath )
			current_build.args.append( ("-cp" , abs_classpath ) )
	
	if len(current_build.classpaths) == 0:
		log("no classpaths")
		current_build.classpaths.append( build_path )
		current_build.args.append( ("-cp" , build_path ) )

	builds.append( current_build )

	return builds

def find_hxmls( folder ) :
	
	builds = []
	hxmls = glob.glob( os.path.join( folder , "*.hxml" ) )
	for hxml in hxmls:
		mtime = os.path.getmtime(hxml)
		if hxml in hxml_cache:
			
			if (mtime > hxml_cache[hxml][1]): # modified
				current = hxml_to_builds(hxml, folder)
				hxml_cache[hxml] = (current, mtime)
			else: # already in cache
				current = hxml_cache[hxml][0]

		else: # not in cache
			current = hxml_to_builds(hxml, folder)
			hxml_cache[hxml] = (current, mtime)

		builds.extend(current)
		
	return builds

extract_tag = re.compile("<([a-z0-9_-]+).*\s(name|main)=\"([a-z0-9_./-]+)\"", re.I)


def find_nmmls( folder ) :
	nmmls = glob.glob( os.path.join( folder , "*.nmml" ) )

	builds = []

	for build in nmmls:
		current_build = HaxeBuild()
		current_build.hxml = build
		current_build.nmml = build
		build_path = os.path.dirname(build)

		# TODO delegate compiler options extractions to NME 3.2:
		# runcmd("nme diplay project.nmml nme_target")

		outp = "NME"
		f = codecs.open( build , "r+", "utf-8" , "ignore" )
		while 1:
			l = f.readline() 
			if not l : 
				break;
			m = extract_tag.search(l)
			if not m is None:
				#print(m.groups())
				tag = m.group(1)
				name = m.group(3)
				if (tag == "app"):
					current_build.main = name
					mFile = re.search("\\b(file|title)=\"([a-z0-9_-]+)\"", l, re.I)
					if not mFile is None:
						outp = mFile.group(2)
				elif (tag == "haxelib"):
					current_build.libs.append( hxlib.HaxeLib.get( name ) )
					current_build.args.append( ("-lib" , name) )
				elif (tag == "classpath"):
					current_build.classpaths.append( os.path.join( build_path , name ) )
					current_build.args.append( ("-cp" , os.path.join( build_path , name ) ) )
			else: # NME 3.2
				mPath = re.search("\\bpath=\"([a-z0-9_-]+)\"", l, re.I)
				if not mPath is None:
					#print(mPath.groups())
					path = mPath.group(1)
					current_build.classpaths.append( os.path.join( build_path , path ) )
					current_build.args.append( ("-cp" , os.path.join( build_path , path ) ) )
		
		outp = os.path.join( folder , outp )
		current_build.target = "cpp"
		current_build.args.append( ("--remap", "flash:nme") )
		current_build.args.append( ("-cpp", outp) )
		current_build.output = outp

		if current_build.main is not None :
			builds.append( current_build )
	return builds




class HaxeBuild :


	def __init__(self) :
		self.std_classes = []
		self.show_times = False
		self.std_packs = []
		self.args = []
		self.main = None
		self.target = None
		self.output = "dummy.js"
		self.hxml = None
		self.nmml = None
		self.classpaths = []
		self.libs = []
		self.classes = None
		self.packages = None
		self.update_time = None
 
	def set_main(self, main):
		self.main = main
	
	def get_name (self):
		if self.main == None:
			return "[No Main]"
		else:
		 	return self.main

	def set_std_classes(self, std_classes):
		self.std_classes = std_classes

	def set_std_packs(self, std_packs):
		self.std_packs = std_packs

	def equals (self, other):
		
		return (self.args == other.args 
			and self.main == other.main
			and self.target == other.target
			and self.output == other.output
			and self.hxml == other.hxml
			and self.nmml == other.nmml
			and self.classpaths == other.classpaths
			and self.libs == other.libs
			and self.show_times == other.show_times)
		   
		

	def copy (self):
		hb = HaxeBuild()
		hb.args = list(self.args)
		hb.main = self.main
		hb.target = self.target
		hb.output = self.output
		hb.hxml = self.hxml
		hb.nmml = self.nmml
		hb.classpaths = list(self.classpaths)
		hb.libs = list(self.libs)
		hb.classes = list(self.classes) if self.classes is not None else None
		hb.packages = list(self.packages) if self.packages is not None else None
		hb.show_times = self.show_times
		return hb

	def get_build_folder (self):
		r = None
		if self.hxml is not None:
			r = os.path.dirname(self.hxml)
		elif self.nmml is not None:
			r = os.path.dirname(self.nmml)

		return r
	

	def set_build_cwd (self):
		self.set_cwd(self.get_build_folder())
	def add_classpath (self, cp):
		
		self.classpaths.append(cp)
		self.args.append(("-cp", cp))
	
	def get_classpath (self, file):
		cps = list(self.classpaths)
		build_folder = self.get_build_folder()
		cps.append(build_folder)
		for cp in cps:
			if file.startswith(cp):
				return cp

		return None

	def is_file_in_classpath (self, file):
		return self.get_classpath(file) is not None

	def get_relative_path (self, file):
		cp = self.get_classpath(file)
		if cp is not None:
			return file.replace(cp, "")[1:]
		else:
			return None

	def to_string(self) :
		out = os.path.basename(self.output)
		if self.nmml is not None:
			return "{out} ({target})".format(self=self, out=out, target=hxconfig.nme_target[0]);
		else:
			return "{main} ({target}:{out})".format(self=self, out=out, main=self.get_name(), target=self.target);
		#return "{self.main} {self.target}:{out}".format(self=self, out=out);
	
	def make_hxml( self ) :
		outp = "# Autogenerated "+self.hxml+"\n\n"
		outp += "# "+self.to_string() + "\n"
		outp += "-main "+ self.main + "\n"
		for a in self.args :
			outp += " ".join( list(a) ) + "\n"
		
		d = os.path.dirname( self.hxml ) + "/"
		
		# relative paths
		outp = outp.replace( d , "")
		outp = outp.replace( "-cp "+os.path.dirname( self.hxml )+"\n", "")

		outp = outp.replace("--no-output " , "")
		outp = outp.replace("-v" , "")

		outp = outp.replace("dummy" , self.main.lower() )

		#print( outp )
		return outp.strip()


	def update_types(self):

		#haxe.output_panel.HaxePanel.status("haxe-debug", "updating types")
		log("update types for " + str(self.classpaths))		
		classes, packages = hxtypes.find_types(self.classpaths, self.libs, os.path.dirname( self.hxml ), [], [], include_private_types = False )

		self.classes = classes;
		self.packages = packages;

	def set_cwd (self, cwd):
		self.args.append(("--cwd" , cwd ))

	def set_times (self):
		self.show_times = True
		self.args.append(("--times", ""))
		self.args.append(("-D", "macro-times"))
		self.args.append(("-D", "macro_times"))

	def set_server_mode (self, server_port = 6000):
		self.args.append(("--connect" , str(server_port)))

	def get_command_args (self, haxe_path):
		cmd = [haxe_path]
		for a in self.args :
			cmd.extend( list(a) )

		if self.main != None:
			cmd.append("-main")
			cmd.append(self.main)
		return cmd

	

	def set_auto_completion (self, display, macro_completion = False, no_output = True):
		
		args = self.args
		print(args)
		self.main = None
		def filterTargets (x):
			return x[0] != "-cs" and x[0] != "-x" and x[0] != "-js" and x[0] != "-php" and x[0] != "-cpp" and x[0] != "-swf" and x[0] != "-java"

		if macro_completion:
			args = list(filter(filterTargets, args ))
		else:
			args = list(map(lambda x : ("-neko", x[1]) if x[0] == "-x" else x, args))

		def filter_commands_and_dce (x):
			return x[0] != "-cmd" and x[0] != "-dce"



		args = list(filter(filter_commands_and_dce, args ))

		if not self.show_times:
			def filter_times (x):
				return x[0] != "--times"
			args = list(filter(filter_times, args))

		print(args)

		if (macro_completion) :
			args.append(("-neko", "__temp.n"))

		
		args.append( ("--display", display ) )
		if (no_output):
			args.append( ("--no-output" , "") )

		self.args = args


	def get_types( self ) :
		now = time.time()
		log("get_types" + str(now))
		log("get_types" + str(self.update_time))
		if self.classes is None or self.packages is None or self.update_time is None or (now - self.update_time) > 10:
			log("update types")
			self.update_time = now
			self.update_types()

		return self.classes, self.packages

	
	def prepare_run (self, haxe_exec, server_mode, view, project):
		b = self.copy()
		
		nekox_file_name = None
		
		for i in range(0, len(b.args)):
			if b.args[i][0] == "-x":
				nekox_file_name = b.args[i][1] + ".n"
				b.args[i] = ("-neko", nekox_file_name)

		if server_mode:
			project.start_server( view )
			b.set_server_mode(project.server.get_server_port())

		
		b.set_build_cwd()
		cmd = b.get_command_args(haxe_exec)



		
		return (cmd, self.get_build_folder(), nekox_file_name)

	def run_async (self, project, view, callback):

		# get environment
		server_mode = project.is_server_mode()
		
		haxe_exec = project.haxe_exec(view)
		env = project.haxe_env(view)

    	

		cmd, build_folder, nekox_file_name = self.prepare_run(haxe_exec, server_mode, view, project)
		
		def cb (out, err):

			
			cmd_and_env = " "
			for k in env:
				if is_st3:
					cmd_and_env = cmd_and_env + "\nset " + k + "=" + str(env[k])
				else:
					cmd_and_env = cmd_and_env + "\nset " + k + "=" + env[k]
			cmd_and_env = cmd_and_env + "\n" + " ".join(cmd);
			log(cmd_and_env)
			log("---------cmd------------")
			log("-------------------------------------")
			
			log("out:" + out)
			log("err:" + err)
			log("---------compiler-output-------------")
			if nekox_file_name is not None:
				self.run_neko_x(build_folder, nekox_file_name)
			callback(out, err)

		run_cmd_async( args=cmd, input="", cwd=build_folder, env=env, callback=cb )
		
		

	def run(self, project, view, async, callback):
		if async:
			log("RUN ASYNC COMPLETION")
			self.run_async( project, view, callback )
		else:
			log("RUN SYNC COMPLETION")
			out, err = self.run_sync( project, view )
			callback(out, err)

	def run_sync (self, project, view):
		# get environment
		server_mode = project.is_server_mode()
		
		haxe_exec = project.haxe_exec(view)
		env = project.haxe_env(view)
		cmd, build_folder, nekox_file_name = self.prepare_run(haxe_exec, server_mode, view, project)
		
		
		log("" + " ".join(cmd))
		for k in env:
			log("set " + k + "=" + env[k])
		log("---------cmd------------")
		
		
		out, err = run_cmd( args=cmd, input="", cwd=build_folder, env=env )
		log("-------------------------------------")
		log("out:" + out)
		log("err:" + err)
		log("---------compiler-output-------------")
		# execute compiled file if hxml/build has -x target
		if nekox_file_name is not None:
			self.run_neko_x(build_folder, nekox_file_name)
		return out,err

	def run_neko_x(self, build_folder, neko_file_name):
		neko_file = os.path.join(build_folder, neko_file_name)
		log("run nekox: " + neko_file) 
		out1, err1 = run_cmd(["neko", neko_file])
		hxpanel.default_panel().writeln(out1)
		hxpanel.default_panel().writeln(err1)
		


