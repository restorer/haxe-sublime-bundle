
import os
from haxe.config import Config
import haxe.types as hxtypes
import haxe.lib as hxlib
import glob
import codecs
import sublime
from haxe.settings import HaxeSettings 
import re

from haxe.haxe_exec import runcmd


hxml_cache = {}

def find_hxml( folder ) :
	print "find_hxml"
	builds = []
	hxmls = glob.glob( os.path.join( folder , "*.hxml" ) )
	for build in hxmls:
		new_build = HaxeBuild()
		if build in hxml_cache:
			cached = hxml_cache[build]
			if cached.equals(new_build):
				print "builds equal"
				currentBuild = cached
				print "builds differ"
			else:
				hxml_cache[build] = new_build
				currentBuild = new_build

		currentBuild = HaxeBuild()
		currentBuild.hxml = build
		buildPath = os.path.dirname(build);

		# print("build file exists")
		f = codecs.open( build , "r+" , "utf-8" , "ignore" )
		while 1:
			l = f.readline() 
			if not l : 
				break;
			if l.startswith("--next") :
				builds.append( currentBuild )
				currentBuild = HaxeBuild()
				currentBuild.hxml = build
				
			l = l.strip()
			
			if l.startswith("-main") :
				spl = l.split(" ")
				if len( spl ) == 2 :
					currentBuild.main = spl[1]
				else :
					sublime.status_message( "Invalid build.hxml : no Main class" )
			
			if l.startswith("-lib") :
				spl = l.split(" ")
				if len( spl ) == 2 :
					lib = hxlib.HaxeLib.get( spl[1] )
					currentBuild.libs.append( lib )
				else :
					sublime.status_message( "Invalid build.hxml : lib not found" )

			if l.startswith("-cmd") :
				spl = l.split(" ")
				currentBuild.args.append( ( "-cmd" , " ".join(spl[1:]) ) )

			#if l.startswith("--connect") and HaxeComplete.instance().serverMode :
			#	currentBuild.args.append( ( "--connect" , str(self.serverPort) ))
			
			for flag in [ "lib" , "D" , "swf-version" , "swf-header", "debug" , "-no-traces" , "-flash-use-stage" , "-gen-hx-classes" , "-remap" , "-no-inline" , "-no-opt" , "-php-prefix" , "-js-namespace" , "-interp" , "-macro" , "-dead-code-elimination" , "-remap" , "-php-front" , "-php-lib", "-dce" , "-js-modern" ] :
				if l.startswith( "-"+flag ) :
					currentBuild.args.append( tuple(l.split(" ") ) )
					
					break
			
			for flag in [ "resource" , "xml" , "x" , "swf-lib" ] :
				if l.startswith( "-"+flag ) :
					spl = l.split(" ")
					outp = os.path.join( folder , " ".join(spl[1:]) )
					currentBuild.args.append( ("-"+flag, outp) )
					
					break

			for flag in HaxeBuild.targets :
				if l.startswith( "-" + flag + " " ) :
					spl = l.split(" ")
					#outp = os.path.join( folder , " ".join(spl[1:]) ) 
					outp = " ".join(spl[1:]) 
					currentBuild.args.append( ("-"+flag, outp) )
					
					currentBuild.target = flag
					currentBuild.output = outp
					break

			if l.startswith("-cp "):
				cp = l.split(" ")
				#view.set_status( "haxe-status" , "Building..." )
				cp.pop(0)
				classpath = " ".join( cp )
				
				absClasspath = os.path.join( buildPath , classpath )
				normAbsClasspath = os.path.normpath(absClasspath)
				currentBuild.classpaths.append( normAbsClasspath )
				currentBuild.args.append( ("-cp" , normAbsClasspath ) )
		
		if len(currentBuild.classpaths) == 0:
			print "no classpaths"
			currentBuild.classpaths.append( buildPath )
			currentBuild.args.append( ("-cp" , buildPath ) )
		
		if currentBuild.main is not None :
			builds.append( currentBuild )
	return builds

extractTag = re.compile("<([a-z0-9_-]+).*\s(name|main)=\"([a-z0-9_./-]+)\"", re.I)


def find_nmml( folder ) :
	nmmls = glob.glob( os.path.join( folder , "*.nmml" ) )

	builds = []

	for build in nmmls:
		currentBuild = HaxeBuild()
		currentBuild.hxml = build
		currentBuild.nmml = build
		buildPath = os.path.dirname(build)

		# TODO delegate compiler options extractions to NME 3.2:
		# runcmd("nme diplay project.nmml nme_target")

		outp = "NME"
		f = codecs.open( build , "r+", "utf-8" , "ignore" )
		while 1:
			l = f.readline() 
			if not l : 
				break;
			m = extractTag.search(l)
			if not m is None:
				#print(m.groups())
				tag = m.group(1)
				name = m.group(3)
				if (tag == "app"):
					currentBuild.main = name
					mFile = re.search("\\b(file|title)=\"([a-z0-9_-]+)\"", l, re.I)
					if not mFile is None:
						outp = mFile.group(2)
				elif (tag == "haxelib"):
					currentBuild.libs.append( hxlib.HaxeLib.get( name ) )
					currentBuild.args.append( ("-lib" , name) )
				elif (tag == "classpath"):
					currentBuild.classpaths.append( os.path.join( buildPath , name ) )
					currentBuild.args.append( ("-cp" , os.path.join( buildPath , name ) ) )
			else: # NME 3.2
				mPath = re.search("\\bpath=\"([a-z0-9_-]+)\"", l, re.I)
				if not mPath is None:
					#print(mPath.groups())
					path = mPath.group(1)
					currentBuild.classpaths.append( os.path.join( buildPath , path ) )
					currentBuild.args.append( ("-cp" , os.path.join( buildPath , path ) ) )
		
		outp = os.path.join( folder , outp )
		currentBuild.target = "cpp"
		currentBuild.args.append( ("--remap", "flash:nme") )
		currentBuild.args.append( ("-cpp", outp) )
		currentBuild.output = outp

		if currentBuild.main is not None :
			builds.append( currentBuild )
	return builds



class HaxeBuild :

	#auto = None
	targets = Config.targets
	nme_targets = Config.nme_targets
	nme_target = Config.nme_target

	def __init__(self) :
		self.std_classes = []
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
			and self.libs == other.libs)
		   
		

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
		for cp in self.classpaths:
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
			return "{out} ({target})".format(self=self, out=out, target=HaxeBuild.nme_target[0]);
		else:
			return "{main} ({target}:{out})".format(self=self, out=out, main=self.main, target=self.target);
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

		classes, packages = hxtypes.find_types(self.classpaths, self.libs, os.path.dirname( self.hxml ), [], [] )

		self.classes = classes;
		self.packages = packages;

	def set_cwd (self, cwd):
		self.args.append(("--cwd" , cwd ))

	def set_times (self):
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

	

	def set_auto_completion (self, display, macro_completion = False):
		
		args = self.args
		self.main = None
		def filterTargets (x):
			return x[0] != "-cs" and x[0] != "-x" and x[0] != "-js" and x[0] != "-php" and x[0] != "-cpp" and x[0] != "-swf" and x[0] != "-java"

		if macro_completion:
			args = filter(filterTargets, args )	
		else:
			args = map(lambda x : ("-neko", x[1]) if x[0] == "-x" else x, args)

		args = args

		if (macro_completion) :
			args.append(("-neko", "__temp.n"))


		args.append( ("--display", display ) )
		args.append( ("--no-output" , "") )

		self.args = args


	def get_types( self ) :
		if self.classes is None or self.packages is None :
			self.update_types()

		return self.classes, self.packages

	def run (self, haxeExec, serverMode, view, project):
		b = self.copy()
		
		is_x = None
		
		for i in range(0, len(b.args)):
			if b.args[i][0] == "-x":
				is_x = b.args[i][1] + ".n"
				b.args[i] = ("-neko", is_x)
				


		

		# ignore servermode when -x
		print b.target
		if serverMode:
			project.start_server( view )
			b.set_server_mode(project.server.get_server_port())

		
		b.set_build_cwd()
		cmd = b.get_command_args(haxeExec)

		print "cmd : " + " ".join(cmd)

		libPath = HaxeSettings.haxeLibraryPath();
		env = os.environ.copy()
		if libPath != None :
			absLibPath = os.path.normpath(os.path.join(self.get_build_folder(), libPath))
			env["HAXE_LIBRARY_PATH"] = absLibPath


			print "cwd:" + self.get_build_folder()
			print "hxml:" + self.hxml
		res, err = runcmd( args=cmd, input="", cwd=self.get_build_folder(), env=env )

		if is_x is not None:
			neko_file = os.path.join(self.get_build_folder(), is_x)
			print neko_file
			res1, err1 = runcmd(["neko", neko_file])
			print res1
			#print err1
		return res,err

