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

	log("read build file:" + build)
	# print("build file exists")
	f = codecs.open( build , "r+" , "utf-8" , "ignore" )
	while 1:
		l = f.readline() 
		if not l : 
			break;
		log(l)
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
				current_build.add_arg( tuple(l.split(" ") ) )
				
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

def find_hxml_projects( folder ) :
	
	builds = []
	hxmls = glob.glob( os.path.join( folder , "*.hxml" ) )
	for hxml in hxmls:
		log(hxml)
		if not hxml.startswith(os.path.join(folder,  "_nme__")):
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

extract_tag = re.compile("<([a-z0-9_-]+).*?\s(name|main|title|file)=\"([ a-z0-9_./-]+)\"", re.I)


def find_nme_project_title(nmml):
	f = codecs.open( nmml , "r+", "utf-8" , "ignore" )
	title = ["No Title"]
	while 1:
		l = f.readline()
		if not l :
			break
		m = extract_tag.search(l)
		if not m is None:
			log(m.groups())
			#print(m.groups())
			tag = m.group(1)
			
			if tag == "meta" or tag == "app" :
				mFile = re.search("\\b(file|title)=\"([ a-z0-9_-]+)\"", l, re.I)
				if not mFile is None:
					title = mFile.group(2)
					break
	f.close()
	return title
			

def find_nme_projects( folder ) :
	nmmls = glob.glob( os.path.join( folder , "*.nmml" ) )
	builds = []
	for nmml in nmmls:
		title = find_nme_project_title(nmml)
		for t in hxconfig.nme_targets:

			builds.append(NmeBuild(title, nmml, t))
	return builds

def find_openfl_projects( folder ) :
	nmmls = glob.glob( os.path.join( folder , "*.xml" ) )
	builds = []
	for nmml in nmmls:
		title = find_nme_project_title(nmml)
		if title != None:
			for t in hxconfig.nme_targets:
				builds.append(OpenFlBuild(title, nmml, t))


	return builds


def create_haxe_build_from_nmml (target, nmml):

	cmd = ["nme", "display"]
	cmd.append(target.target)
	cmd.extend(target.args)

	nmml_dir = os.path.dirname(nmml)

	log("CMD: " + " ".join(cmd))

	out, err = run_cmd( cmd, cwd=nmml_dir )

	log("OUT: " + out)




	#f = codecs.open( hxml_file , "wb" , "utf-8" , "ignore" )

	# write out to file
	hxml_file = os.path.join(nmml_dir, target.hxml_name)
	f = codecs.open( hxml_file , "wb" , "utf-8" , "ignore" )
	f.write( out )
	f.close()
	

	hx_build = hxml_to_builds(hxml_file, nmml_dir)[0]
	hx_build.nmml = nmml
	return hx_build




class NmeBuild :


	def __init__(self, title, nmml, target, cb = None):
		self._title = title
		self.current_target = target
		self.nmml = nmml
		self._current_build = cb

		#log("CLASSPATHS:" + str(self.current_build.classpaths))

	@property
	def title(self):
		return self._title
	@property
	def build_file(self):
		return self.nmml


	@property
	def target(self):
		return self.current_build.target

	@property
	def current_build (self):
		if self._current_build == None:
			self._current_build = create_haxe_build_from_nmml(self.current_target, self.nmml)

		return self._current_build
	
	def to_string(self) :
		#out = os.path.basename(self.current_build.output)
		out = self.title
		return "{out} ({target})".format(out=out, target=self.current_target.name);
		


	def filter_platform_specific(self, packs_or_classes):
		res = []
		for c in packs_or_classes:
			if not c.startswith("native") and not c.startswith("browser") and not c.startswith("flash") and not c.startswith("flash9") and not c.startswith("flash8"):
				res.append(c)

		return res

	def get_types(self):
		classes, packages = self._current_build.get_types()

		res = self.filter_platform_specific(classes), self.filter_platform_specific(packages)

		log(str(res))
		return res
		

	@property
	def std_classes(self):
		return self.filter_platform_specific(self._current_build.std_classes)
		

	@property
	def std_packs(self):
		return self.filter_platform_specific(self._current_build.std_packs)

	def copy (self):
		r = NmeBuild(self.title, self.nmml, self.current_target, self.current_build.copy())
		
		return r

	def get_relative_path(self, file):
		return self.current_build.get_relative_path(file)

	def get_build_folder(self):
		return self.current_build.get_build_folder()

	

	def set_auto_completion(self, display, macro_completion):
		self.current_build.set_auto_completion(display, macro_completion)

	def set_times(self):
		self.current_build.set_times()

	def is_nme (self):
		return True



	def add_classpath(self, cp):
		self.current_build.add_classpath(cp)

	def run(self, project, view, async, on_result):
		self.current_build.run(project, view, async, on_result)

	def run_sync (self, project, view):
		return self.current_build.run_sync(project, view)		
	

	def get_build_command(self):
		return ["nme"]

	def prepare_sublime_build_cmd (self, project, server_mode, view):
		
		

		cmd = self.get_build_command()
		cmd.append(self.current_target.build_command)
		cmd.append(self.current_target.target)
		cmd.extend(self.current_target.args)
		

		# if server_mode:
		# 	project.start_server( view )
		# 	cmd.append("--connect")
		# 	cmd.append(str(project.server.get_server_port()))
		


		return (cmd, self.get_build_folder())


	def prepare_run(self, project, server_mode, view):
		return self.current_build.prepare_run(project, server_mode, view)

	@property
	def classpaths (self):
		return self.current_build.classpaths

	@property
	def args (self):
		return self.current_build.args

class OpenFlBuild (NmeBuild):

	def __init__(self, title, nmml, target, cb = None):
		super(title, nmml, target, cb)

	def filter_platform_specific(self, packs_or_classes):
		res = []
		for c in packs_or_classes:
			# allow only flash package
			if not c.startswith("native") and not c.startswith("browser"):
				res.append(c)

		return res

	def get_build_command(self):
		return ["openfl"]

class HaxeBuild :

	def __init__(self) :
		
		self.show_times = False
		self.std_classes = []
		self.std_packs = []
		self.args = []
		self.main = None
		self.target = None
		self.output = "dummy.js"
		self.hxml = None
		self.nmml = None
		self.openfl = False
		self.classpaths = []
		self.libs = []
		self.classes = None
		self.packages = None
		self.update_time = None
		self.mode_completion = False
		
	@property
	def title(self):
		return self.output

	@property
	def build_file(self):
		return self.hxml

	def is_nme (self):
		return self.nmml != None

	def is_openfl (self):
		return self.openfl == True

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
			and self.show_times == other.show_times
			and self.mode_completion == other.mode_completion)
		   
		

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
		hb.mode_completion = self.mode_completion
		return hb

	def add_arg(self, arg):
		self.args.append(arg)

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
		
		
		for cp in cps:
			if file.startswith(cp):
				return cp

		build_folder = self.get_build_folder()
		if file.startswith(build_folder):
			return build_folder
		
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
		cmd = list(haxe_path)

		

		for a in self.args :
			cmd.extend( list(a) )

		#for l in self.libs :
		#	cmd.append( ("-lib", l) )

		if self.main != None:
			cmd.append("-main")
			cmd.append(self.main)
		return cmd

	

	def set_auto_completion (self, display, macro_completion = False, no_output = True):
		
		self.mode_completion = True

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


	def update_types(self):

		#haxe.output_panel.HaxePanel.status("haxe-debug", "updating types")
		log("update types for " + str(self.classpaths))		
		classes, packages = hxtypes.find_types(self.classpaths, self.libs, os.path.dirname( self.hxml ), [], [], include_private_types = False )

		self.classes = classes;
		self.packages = packages;


	def get_types( self ) :
		now = time.time()
		
		if self.classes is None or self.packages is None or self.update_time is None or (now - self.update_time) > 10:

			self.update_time = now
			self.update_types()

		return self.classes, self.packages

	
	def prepare_sublime_build_cmd (self, project, server_mode, view):
		r = self.prepare_run(project, server_mode, view)
		return (r[0], r[1])

	def prepare_run (self, project, server_mode, view):
		run_exec = self.get_run_exec(project)
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
		cmd = b.get_command_args(run_exec)

		return (cmd, self.get_build_folder(), nekox_file_name)

	def get_run_exec(self, project):
		return project.haxe_exec()

	def run_async (self, project, view, callback):

		# get environment
		server_mode = project.is_server_mode()
		
		

		env = project.haxe_env(view)

    	


		cmd, build_folder, nekox_file_name = self.prepare_run(project, server_mode, view)
		
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
		
		
		env = project.haxe_env(view)
		cmd, build_folder, nekox_file_name = self.prepare_run(project, server_mode, view)
		
		
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
		


