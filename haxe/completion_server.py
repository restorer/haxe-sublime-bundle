
import haxe.settings
import os
import haxe.project



import sublime

from subprocess import Popen
from startup import STARTUP_INFO

class CompletionServer ():
	def __init__ (self, port, serverMode):
		self.serverProc = None
		self.serverPort = port
		self.serverMode = serverMode


	def start_server( self , view = None ) : 
		#self.stop_server()	
		if self.serverMode and self.serverProc is None :
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

				cmd = [haxepath , "--wait" , str(self.serverPort) ]
				#self.serverProc = Popen(cmd, env=env , startupinfo=STARTUP_INFO)
				self.serverProc = Popen(cmd, cwd=cwd, env = merged_env, startupinfo=STARTUP_INFO)
				self.serverProc.poll()
			except(OSError, ValueError) as e:
				err = u'Error starting server %s: %s' % (" ".join(cmd), e)
				sublime.error_message(err)
	
	def stop_server( self ) :
		
		proc = self.serverProc

		if proc is not None :
			proc.terminate()
			proc.kill()
			proc.wait()
		
		self.serverProc = None
		del self.serverProc