import re
import os
import sublime, sublime_plugin
import functools

is_st3 = int(sublime.version()) >= 3000

if is_st3:
	import Haxe.haxe.settings as hxsettings
	import Haxe.haxe.types as hxtypes
	from Haxe.haxe.log import log

	from Haxe.haxe.execute import run_cmd
else:
	import haxe.settings as hxsettings
	import haxe.types as hxtypes
	from haxe.log import log

	from haxe.execute import run_cmd

libLine = re.compile("([^:]*):[^\[]*\[(dev\:)?(.*)\]")

class HaxeLibManager:
	
	def __init__(self, project):
		self._available = {}
		self.basePath = None
		self.scanned = False
		self.project = project


	@property
	def available (self):
		if not self.scanned:
			self.scan()
		return self._available

	def get( self, name ) :
		if( name in self.available.keys()):
			return self.available[name]
		else :
			sublime.status_message( "Haxelib : "+ name +" project not installed" )
			return None

	
	def get_completions(self) :
		comps = []
		for l in self.available :
			lib = self.available[l]
			comps.append( ( lib.name + " [" + lib.version + "]" , lib.name ) )

		return comps

	
	def scan(self) :
		self.scanned = True
		log("do scan")
		cmd = self.project.haxelib_exec()
		cmd.append("config")
		hlout, hlerr = run_cmd( cmd )
		self.basePath = hlout.strip()

		self._available = {}

		cmd = self.project.haxelib_exec()
		cmd.append("list")

		hlout, hlerr = run_cmd( cmd )

		for l in hlout.split("\n") :
			found = libLine.match( l )
			if found is not None :
				name, dev, version = found.groups()
				lib = HaxeLib( self, name , dev is not None , version )

				self._available[ name ] = lib

	def install_lib(self, lib):
		cmd = self.project.haxelib_exec()
		cmd.append("install")
		cmd.append(lib)
		run_cmd(cmd)
		self.scan()

	def remove_lib(self, lib):
		cmd = self.project.haxelib_exec()
		cmd.append("remove")
		cmd.append(lib)
		run_cmd(cmd)
		self.scan()


	def upgrade_all(self):
		cmd = self.project.haxelib_exec()
		cmd.append("upgrade")
		run_cmd(cmd)
		self.scan()

	def self_update(self):
		cmd = self.project.haxelib_exec()
		cmd.append("selfupdate")
		run_cmd(cmd)
		self.scan()

	def search_libs(self):
		cmd = self.project.haxelib_exec()
		cmd.append("search")
		cmd.append(" ")
		out,err = run_cmd(cmd);
		return self._collect_libraries(out)

	def _collect_libraries(self, out):
		return out.splitlines()[0:-1]

	def is_lib_installed(self, lib):
		return lib in self.available
	
	def get_lib(self, lib):
		return self.available[lib]

class HaxeLib :

	def __init__( self , manager, name , dev , version ):
		self.name = name
		self.dev = dev
		self.version = version
		self.classes = None
		self.packages = None
 
		if self.dev :
			self.path = self.version
			self.version = "dev"
		else : 
			self.path = os.path.join( manager.basePath , self.name , ",".join(self.version.split(".")) )
 

	def as_cmd_arg (self):
		return self.name + ":" + self.version

	def extract_types( self ):

		if self.dev is True or ( self.classes is None and self.packages is None ):
			self.classes, self.packages = hxtypes.extract_types( self.path )
		
		return self.classes, self.packages

	




class HaxeInstallLib( sublime_plugin.WindowCommand ):

	

	def prepare_menu (self, libs, manager):
		menu = []
		for l in libs :
			if manager.is_lib_installed(l):
				menu.append( [ l + " [" + manager.get_lib(l).version + "]" , "Remove" ] )
			else :
				menu.append( [ l , 'Install' ] )

		menu.append( ["Upgrade libraries", "Upgrade installed libraries"] )
		menu.append( ["Haxelib Selfupdate", "Updates Haxelib itself"] )
		
		return menu

	def run(self):
		if is_st3:
			import Haxe.haxe.project as hxproject
		else:
			import haxe.project as hxproject

		project = hxproject.current_project(sublime.active_window().active_view())
		manager = project.haxelib_manager
		
		libs = manager.search_libs()

		menu = self.prepare_menu(libs, manager)

		on_selected = functools.partial(self.install, libs, project)

		self.window.show_quick_panel(menu, on_selected)

	def install( self, libs, project, i ):

		if i < 0 :
			return
		manager = project.haxelib_manager
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
		

