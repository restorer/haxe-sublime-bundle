import sublime
import sys
import os
from subprocess import Popen, PIPE

from haxe.startup import STARTUP_INFO
from haxe.log import log

class Server ():
	def __init__ (self, port):
		self._server_proc = None
		self._server_port = port
		self._orig_server_port = port

	def get_server_port (self):
		return self._server_port

	def start( self , haxe_path, cwd = None, env = None, retries = 10 ) : 
		if self._server_proc is None : 
			try:
				cmd = [haxe_path , "--wait" , str(self._server_port) ]

				if env == None:
					env = os.environ.copy()

				self._server_proc = Popen(cmd, cwd=cwd, env = env, stdout=PIPE, stderr=PIPE, startupinfo=STARTUP_INFO)
				poll_res = self._server_proc.poll()
				
				log("server started at port: " + str(self._server_port))
				
			except(OSError, ValueError) as e:
				err = u'Error starting server %s: %s' % (" ".join(cmd), e)
				sublime.error_message(err)
				if (retries > 0):
					self.stop();
					self._server_port += 1
					log("retry starting server at port: " + str(self._server_port))
					self.start(haxe_path, cwd, env, retries-1)
				else:
					msg = "Cannot start haxe compilation server on ports {0}-{1}"
					msg = msg.format((self._orig_server_port, self._server_port))
					log("Server starting error")
					hxpanel.default_panel().writeln(msg)
					sublime.error_message(msg)
			
	def stop( self ) :
		try:
			proc = self._server_proc

			if proc is not None :
				proc.terminate()
				proc.kill()
				proc.wait()
		except:
			pass
		
		self._server_proc = None
