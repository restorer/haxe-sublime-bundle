


import sublime
from haxe.log import log
from subprocess import Popen
from haxe.startup import STARTUP_INFO

class Server ():
	def __init__ (self, port):
		self._server_proc = None
		self._server_port = port


	def get_server_port (self):
		return self._server_port

	def start( self , haxe_path, cwd = None, env = None, retries = 3 ) : 
		if self._server_proc is None : 
			try:
				cmd = [haxe_path , "--wait" , str(self._server_port) ]
				self._server_proc = Popen(cmd, cwd=cwd, env = env, startupinfo=STARTUP_INFO)
				self._server_proc.poll()
				log("server started at port: " + str(self._server_port))
			except(OSError, ValueError) as e:
				err = u'Error starting server %s: %s' % (" ".join(cmd), e)
				sublime.error_message(err)
				if (retries > 0):
					self.stop();
					self._server_port += 1
					log("retry starting server at port: " + str(self._server_port))
					self.start(haxe_path, cwd, env, retries-1)
			
	

	def stop( self ) :
		
		proc = self._server_proc

		if proc is not None :
			proc.terminate()
			proc.kill()
			proc.wait()
		
		self._server_proc = None
