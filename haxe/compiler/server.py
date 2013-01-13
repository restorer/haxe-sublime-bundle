
import haxe.settings
import os
import haxe.project



import sublime

from subprocess import Popen
from haxe.startup import STARTUP_INFO

class Server ():
	def __init__ (self, port):
		self._server_proc = None
		self._server_port = port


	def get_server_port (self):
		return self._server_port

	def start_server( self , view = None ) : 

		if self._server_proc is None : 
			try:
				haxepath = haxe.settings.HaxeSettings.haxeExec(view)
				 
				env = os.environ.copy()

				merged_env = env.copy()
				
				if view is not None :
					user_env = view.settings().get('build_env')
					if user_env:
						merged_env.update(user_env)


				if view is not None :
					
					libPath = haxe.settings.HaxeSettings.haxeLibraryPath()
					if libPath != None :
						merged_env["HAXE_LIBRARY_PATH"] = libPath

					#haxepath = settings.get("haxe_path" , haxepath)
			
				main_folder = haxe.project.Project.main_folder()
				if main_folder == None:
					main_folder = "."

				cwd = main_folder

				cmd = [haxepath , "--wait" , str(self._server_port) ]
				self._server_proc = Popen(cmd, cwd=cwd, env = merged_env, startupinfo=STARTUP_INFO)
				self._server_proc.poll()
			except(OSError, ValueError) as e:
				err = u'Error starting server %s: %s' % (" ".join(cmd), e)
				sublime.error_message(err)
	
	def stop_server( self ) :
		
		proc = self._server_proc

		if proc is not None :
			proc.terminate()
			proc.kill()
			proc.wait()
		
		self._server_proc = None
