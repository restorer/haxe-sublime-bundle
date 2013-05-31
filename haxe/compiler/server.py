import sublime
import sys
import os
import atexit
from subprocess import Popen

is_st3 = int(sublime.version()) >= 3000

if is_st3:
	from Haxe.haxe.startup import STARTUP_INFO
	from Haxe.haxe.log import log
	import Haxe.haxe.panel as hxpanel
else:
	from haxe.startup import STARTUP_INFO
	from haxe.log import log
	import haxe.panel as hxpanel

class Server ():
	def __init__ (self, port):

		self._server_proc = None
		self._server_port = port
		self._orig_server_port = port

		atexit.register(lambda: self.stop())

	def get_server_port (self):
		return self._server_port

	def start( self , haxe_path, cwd = None, env = None, retries = 10 ) : 
		if not hasattr(self, "_server_proc"):
			self._server_proc = None
		
		if self._server_proc is None : 
			try:
				cmd = [haxe_path , "--wait" , str(self._server_port) ]

				full_env = os.environ.copy()

				if env != None:
					for k in env:
						try:
							if is_st3:
								val = env[k]
							else:
								val = unicode(env[k], "ISO-8859-1").encode(sys.getfilesystemencoding())
						except:
							val = env[k].encode(sys.getfilesystemencoding())
						
						full_env[k] = os.path.expandvars(val)
				

				self._server_proc = Popen(cmd, cwd=cwd, env = full_env, startupinfo=STARTUP_INFO)
				self._server_proc.poll()
				#self._server_proc.stderr.close()
				#self._server_proc.stdout.close()
				
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
					#sublime.error_message(msg)
			except Exception as e:
				log(str(e))
		

	
	def stop( self, completeCallback = None) :
		try:
			proc = self._server_proc

			if proc is not None :
				self._server_proc = None
				del self._server_proc
				proc.terminate()
				proc.kill()
				proc.wait()
				proc = None
				del proc
				# running the process on the same port causes zombie processes
				# increment the server port to avoid this
				self._server_port = self._server_port + 1
			
			if completeCallback != None:
				completeCallback()
			
		except:
			pass
	def __del__(self):
		self.stop()
		
		
