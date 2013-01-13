
import haxe.settings
from haxe.haxe_exec import runcmd
import haxe.haxe_complete

import functools



 
import os
import sublime, sublime_plugin


def haxe_settings () :
	return haxe.settings.HaxeSettings
def haxe_exec () :
	return haxe.haxe_exec


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
 
		#print(self.name + " => " + self.path)

	def extract_types( self ):

		if self.dev is True or ( self.classes is None and self.packages is None ):
			self.classes, self.packages = haxe.haxe_complete.HaxeComplete.instance().extract_types( self.path )
		
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
		#print "do scan haxelib"
		hlout, hlerr = runcmd( [haxe_settings().haxeLibExec() , "config" ] )
		HaxeLib.basePath = hlout.strip()

		HaxeLib.available = {}

		hlout, hlerr = runcmd( [haxe_settings().haxeLibExec() , "list" ] )

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
		print "try install lib"
		out,err = runcmd([haxe_settings().haxeLibExec() , "search" , " "]);
		
		libs = self.collect_libraries(out)

		

		menu = self.prepare_menu(libs)

		cb = functools.partial(self.install, libs)

		self.window.show_quick_panel(menu,cb)

	def install( self, libs, i ):
		if i < 0 :
			return

		if i == len(libs) :
			cmd = [haxe_settings().haxeLibExec() , "upgrade" ]
		else :
			lib = libs[i]
			print "lib to install: " + lib
			if lib in HaxeLib.available :
				cmd = [haxe_settings().haxeLibExec() , "remove" , lib ]	
			else :
				cmd = [haxe_settings().haxeLibExec(), "install" , lib ]	

		runcmd(cmd)
