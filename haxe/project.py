
import sublime
import os
import haxe.build as hxbuild

import haxe.output_panel

import haxe.hxtools as hxtools

import haxe.types as hxtypes
from haxe.settings import HaxeSettings

import re

from haxe.haxe_exec import runcmd

import haxe.compiler.server as hxserver

classpathLine = re.compile("Classpath : (.*)")

haxeVersion = re.compile("haxe_([0-9]{3})",re.M)


def msgToPanel (msg) : 
	return haxe.output_panel.normal_panel.write(msg)

def panel () : 
	return haxe.output_panel.HaxePanel

def collect_compiler_info ():
	out, err = runcmd( [HaxeSettings.haxeExec(), "-main", "Nothing", "-v", "--no-output"] )
	print out		
	m = classpathLine.match(out)
	
	classes = []
	packs = []
	stdPaths = []

	if m is not None :
		stdPaths = set(m.group(1).split(";")) - set([".","./"])
	
	for p in stdPaths : 
		#print("std path : "+p)
		if len(p) > 1 and os.path.exists(p) and os.path.isdir(p):
			classes, packs = hxtypes.extract_types( p, [], [] )
			

	ver = re.search( haxeVersion , out )

	return (classes, packs, ver, stdPaths)

class ProjectContext:
	def __init__(self):
		self.currentBuild = None
		self.selectingBuild = False
		self.builds = []
		
		self.server = hxserver.Server(6000)

		self.update_compiler_info()

	def update_compiler_info (self):
		classes, packs, ver, stdPaths = collect_compiler_info()

		self.serverMode = int(ver.group(1)) >= 209

		self.stdPaths = stdPaths
		self.stdPackages = packs
		self.stdClasses = ["Void","String", "Float", "Int", "UInt", "Bool", "Dynamic", "Iterator", "Iterable", "ArrayAccess"]
		self.stdClasses.extend(classes)

	def is_server_mode (self):
		return self.serverMode and HaxeSettings.getBool('haxe-use-server-mode', True)

_ctx = None

def ctx():
	global _ctx
  	if _ctx == None:
  		_ctx = ProjectContext()
  	return _ctx




		


def generate_build(view) :

	fn = view.file_name()

	if ctx().currentBuild is not None and fn == ctx().currentBuild.hxml and view.size() == 0 :	
		e = view.begin_edit()
		hxmlSrc = ctx().currentBuild.make_hxml()
		view.insert(e,0,hxmlSrc)
		view.end_edit(e)


def select_build( view ) :
	scopes = view.scope_name(view.sel()[0].end()).split()
	
	if 'source.hxml' in scopes:
		view.run_command("save")

	extract_build_args( view , True )


# called everytime a view is activated

def extract_build_args( view , forcePanel = False ) :
	
	ctx().builds = []

	fn = view.file_name()


	settings = view.settings()

	print "filename: " + fn

	folder = os.path.dirname(fn)
	

	folders = view.window().folders()
	
	for f in folders:
		ctx().builds.extend(hxbuild.find_hxml(f))
		ctx().builds.extend(hxbuild.find_nmml(f))
			

	
	print "num builds:" + str(len(ctx().builds))

	# settings.set("haxe-complete-folder", folder)
	

	if len(ctx().builds) == 1:
		if forcePanel : 
			sublime.status_message("There is only one build")

		# will open the build file
		#if forcePanel :
		#	b = builds[0]
		#	f = b.hxml
		#	v = view.window().open_file(f,sublime.TRANSIENT) 

		set_current_build( view , int(0), forcePanel )

	elif len(ctx().builds) == 0 and forcePanel :
		sublime.status_message("No hxml or nmml file found")

		f = os.path.join(folder,"build.hxml")

		ctx().currentBuild = None
		get_build(view)
		ctx().currentBuild.hxml = f

		#for whatever reason generate_build doesn't work without transient
		view.window().open_file(f,sublime.TRANSIENT)

		set_current_build( view , int(0), forcePanel )

	elif len(ctx().builds) > 1 and forcePanel :
		buildsView = []
		for b in ctx().builds :
			#for a in b.args :
			#	v.append( " ".join(a) )
			buildsView.append( [b.to_string(), os.path.basename( b.hxml ) ] )

		ctx().selectingBuild = True
		sublime.status_message("Please select your build")
		view.window().show_quick_panel( buildsView , lambda i : set_current_build(view, int(i), forcePanel) , sublime.MONOSPACE_FONT )

	elif settings.has("haxe-build-id"):
		set_current_build( view , int(settings.get("haxe-build-id")), forcePanel )
	
	else:
		set_current_build( view , int(0), forcePanel )


def set_current_build( view , id , forcePanel ) :
	
	print "set_current_build"
	if id < 0 or id >= len(ctx().builds) :
		id = 0
	
	view.settings().set( "haxe-build-id" , id )	

	if len(ctx().builds) > 0 :
		ctx().currentBuild = ctx().builds[id]
		print "set_current_build - 2"
		panel().status( "haxe-build" , ctx().currentBuild.to_string() )
	else:
		panel().status( "haxe-build" , "No build" )
		
	ctx().selectingBuild = False

	if forcePanel and ctx().currentBuild is not None: # choose NME target
		if ctx().currentBuild.nmml is not None:
			sublime.status_message("Please select a NME target")
			nme_targets = []
			for t in hxbuild.HaxeBuild.nme_targets :
				nme_targets.append( t[0] )

			view.window().show_quick_panel(nme_targets, lambda i : select_nme_target(ctx().currentBuild, i, view))


def run_build( view ) :
	
	haxeExec = HaxeSettings.haxeExec(view)
	extract_build_args(view, True)
	build = get_build(view)

	out, err = build.run(haxeExec, ctx().serverMode, view, ctx().server)
	print out
	print err
	print "run_build_complete"
	msgToPanel(err)
	view.set_status( "haxe-status" , "build finished" )
	
	

def select_nme_target( build, i, view ):
	target = hxbuild.HaxeBuild.nme_targets[i]
	if build.nmml is not None:
		hxbuild.HaxeBuild.nme_target = target
		view.set_status( "haxe-build" , build.to_string() )
		panel().status( "haxe-build" , build.to_string() )

def clear_build(  ) :
	ctx().currentBuild = None

def get_build( view ) :
	
	if ctx().currentBuild is None and view.score_selector(0,"source.haxe.2") > 0 :

		fn = view.file_name()

		src_dir = os.path.dirname( fn )

		src = view.substr(sublime.Region(0, view.size()))
	
		build = hxbuild.HaxeBuild()
		build.target = "js"

		folder = os.path.dirname(fn)
		folders = view.window().folders()
		for f in folders:
			if f in fn :
				folder = f

		pack = []
		for ps in hxtools.packageLine.findall( src ) :
			if ps == "":
				continue
				
			pack = ps.split(".")
			for p in reversed(pack) : 
				spl = os.path.split( src_dir )
				if( spl[1] == p ) :
					src_dir = spl[0]

		cl = os.path.basename(fn)
		cl = cl.encode('ascii','ignore')
		cl = cl[0:cl.rfind(".")]

		main = pack[0:]
		main.append( cl )
		build.main = ".".join( main )

		build.output = os.path.join(folder,build.main.lower() + ".js")

		print "add cp: " + src_dir

		build.args.append( ("-cp" , src_dir) )
		#build.args.append( ("-main" , build.main ) )

		build.args.append( ("-js" , build.output ) )
		#build.args.append( ("--no-output" , "-v" ) )

		build.hxml = os.path.join( src_dir , "build.hxml")
		
		#build.hxml = os.path.join( src_dir , "build.hxml")
		ctx().currentBuild = build
		
	return ctx().currentBuild	


class Project():

	@staticmethod
	def folders ():
		return sublime.active_window().folders()


	# could return no folder if project file is not located in a root of a folder
	# or multiple folders if they contain project files
	@staticmethod
	def get_project_folder ():
		found = []
		folders = sublime.active_window().folders()
		print str(folders)
		for folder in folders:
			files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder,f))]
			print str(files)
			for f in files:
				print(os.path.splitext(f))
				if os.path.splitext(f)[1] == ".sublime-project":
					found.append((folder, f))
		
		return found		
		

	@staticmethod
	def main_folder ():
		for f in Project.folders():
			if os.path.exists(f +  "/.haxeproject"):
				return f
		return None

	@staticmethod 
	def create_main_folder ():
		folders1 = Project.folders()

		suggested_folder = folders1[0] if folders1 else os.path.expanduser("~")
		w = sublime.active_window()

		w.show_input_panel("Enter project root:", suggested_folder, Project.main_folder_selected, None, None)


	@staticmethod
	def main_folder_selected (path):
		dir = path + "/.haxeproject"
		os.makedirs(dir)
		

	

		


 
#print Project.create_main_folder()
		