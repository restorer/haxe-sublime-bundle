import re
import os
import sublime, sublime_plugin
import functools

is_st3 = int(sublime.version()) >= 3000

if is_st3:
	import Haxe.haxe.settings as hxsettings
	import Haxe.haxe.types as hxtypes

	from Haxe.haxe.execute import run_cmd
else:
	import haxe.settings as hxsettings
	import haxe.types as hxtypes

	from haxe.execute import run_cmd

libLine = re.compile("([^:]*):[^\[]*\[(dev\:)?(.*)\]")

class HaxeLib :

	available = {}
	basePath = None

	def __init__( self , name , dev , version ):
		self.name = name
		self.dev = dev
		self.version = version
		self.classes = None
		self.packages = None
 
		if self.dev :
			self.path = self.version
			self.version = "dev"
		else : 
			self.path = os.path.join( HaxeLib.basePath , self.name , ",".join(self.version.split(".")) )
 

	def extract_types( self ):

		if self.dev is True or ( self.classes is None and self.packages is None ):
			self.classes, self.packages = hxtypes.extract_types( self.path )
		
		return self.classes, self.packages

	@staticmethod
	def get( name ) :
		if( name in HaxeLib.available.keys()):
			return HaxeLib.available[name]
		else :
			sublime.status_message( "Haxelib : "+ name +" project not installed" )
			return None

	@staticmethod
	def get_completions() :
		comps = []
		for l in HaxeLib.available :
			lib = HaxeLib.available[l]
			comps.append( ( lib.name + " [" + lib.version + "]" , lib.name ) )

		return comps

	@staticmethod
	def scan() :
		hlout, hlerr = run_cmd( [hxsettings.haxelib_exec() , "config" ] )
		HaxeLib.basePath = hlout.strip()

		HaxeLib.available = {}

		hlout, hlerr = run_cmd( [hxsettings.haxelib_Exec() , "list" ] )

		for l in hlout.split("\n") :
			found = libLine.match( l )
			if found is not None :
				name, dev, version = found.groups()
				lib = HaxeLib( name , dev is not None , version )

				HaxeLib.available[ name ] = lib



class HaxeInstallLib( sublime_plugin.WindowCommand ):

	def collect_libraries(self, out):
		return out.splitlines()[0:-1]

	def prepare_menu (self, libs):
		menu = []
		for l in libs :
			if l in HaxeLib.available :
				menu.append( [ l + " [" + HaxeLib.available[l].version + "]" , "Remove" ] )
			else :
				menu.append( [ l , 'Install' ] )

		menu.append( ["Upgrade libraries"] )
		
		return menu

	def run(self):
		print("try install lib")
		out,err = run_cmd([hxsettings.haxelib_exec() , "search" , " "]);
		
		libs = self.collect_libraries(out)

		

		menu = self.prepare_menu(libs)

		cb = functools.partial(self.install, libs)

		self.window.show_quick_panel(menu,cb)

	def install( self, libs, i ):
		if i < 0 :
			return

		haxelib = hxsettings.haxelib_exec
		if i == len(libs) :
			cmd = [haxelib , "upgrade" ]
		else :
			lib = libs[i]
			print("lib to install: " + lib)
			if lib in HaxeLib.available :
				cmd = [haxelib , "remove" , lib ]	
			else :
				cmd = [haxelib, "install" , lib ]	

		run_cmd(cmd)
