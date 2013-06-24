import re
import os
import sublime

from haxe import types as hxtypes

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
		env = self.project.haxe_env()
		log("do scan")
		cmd = self.project.haxelib_exec()
		cmd.append("config")
		hlout, hlerr = run_cmd( cmd, env=env )
		self.basePath = hlout.strip()

		self._available = {}

		cmd = self.project.haxelib_exec()
		cmd.append("list")
		
		hlout, hlerr = run_cmd( cmd, env=env )
		log("haxelib output: " + hlout)
		log("haxelib error: " + hlerr)
		for l in hlout.split("\n") :
			found = libLine.match( l )
			if found is not None :
				name, dev, version = found.groups()
				lib = HaxeLibLibrary( self, name , dev is not None , version )

				self._available[ name ] = lib

	def install_lib(self, lib):
		cmd = self.project.haxelib_exec()
		env = self.project.haxe_env()
		cmd.append("install")
		cmd.append(lib)
		log(str(cmd))
		run_cmd(cmd, env=env)
		self.scan()

	def remove_lib(self, lib):
		cmd = self.project.haxelib_exec()
		env = self.project.haxe_env()
		cmd.append("remove")
		cmd.append(lib)
		log(str(cmd))
		run_cmd(cmd,env=env)
		self.scan()

	def upgrade_all(self):
		cmd = self.project.haxelib_exec()
		env = self.project.haxe_env()
		cmd.append("upgrade")
		log(str(cmd))
		run_cmd(cmd, env=env)
		self.scan()

	def self_update(self):
		cmd = self.project.haxelib_exec()
		env = self.project.haxe_env()
		cmd.append("selfupdate")
		log(str(cmd))
		run_cmd(cmd, env=env)
		self.scan()

	def search_libs(self):
		cmd = self.project.haxelib_exec()
		env = self.project.haxe_env()
		cmd.append("search")
		cmd.append("_")
		log(str(cmd))
		out,err = run_cmd(cmd, env=env);
		return self._collect_libraries(out)

	def _collect_libraries(self, out):
		return out.splitlines()[0:-1]

	def is_lib_installed(self, lib):
		return lib in self.available
	
	def get_lib(self, lib):
		return self.available[lib]

class HaxeLibLibrary :

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
