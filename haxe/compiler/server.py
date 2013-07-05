import sublime
import sys
import os

from subprocess import Popen, PIPE
import time 
from haxe.plugin import is_st3

from haxe.plugin import STARTUP_INFO
from haxe.log import log
from haxe import plugin
from haxe import panel as hxpanel
from haxe import settings as hxsettings

class Server ():
	def __init__ (self, port):

		self._use_wrapper = hxsettings.use_haxe_servermode_wrapper()

		self._server_proc = None
		self._server_port = port
		self._orig_server_port = port


	def get_server_port (self):
		return self._server_port

	def start( self , haxe_path, cwd = None, env = None, retries = 10 ) : 
		if not hasattr(self, "_server_proc"):
			self._server_proc = None
		
		if self._server_proc is None : 
			try:
				
				if self._use_wrapper:
					wrapper = plugin.plugin_base_dir() + "/wrapper"
					cmd = ["neko", wrapper]
				else:
					cmd = list()
				
				cmd.extend([haxe_path , "--wait" , str(self._server_port) ])
				log("start server:")
				
				log(" ".join(cmd))
				full_env = os.environ.copy()
				if env is not None:
					full_env.update(env)
					
				if env is not None:
					for k in env:
						try:
							if is_st3:
								val = env[k]
							else:
								val = unicode(env[k], "ISO-8859-1").encode(sys.getfilesystemencoding())
						except:
							if is_st3:
								val = env[k]
							else:
								val = env[k].encode(sys.getfilesystemencoding())
						

						full_env[k] = os.path.expandvars(val)
				

				log("server env:" + str(full_env))
				self._server_proc = Popen(cmd, cwd=cwd, env=full_env, stdin=PIPE, stdout=PIPE, startupinfo=STARTUP_INFO)
				
				self._server_proc.poll()

				time.sleep(0.05)
					
				log("server started at port: " + str(self._server_port))
				# hxpanel.default_panel().writeln("server started at port: " + str(self._server_port))
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
					#hxpanel.default_panel().writeln(msg)
					#sublime.error_message(msg)
			except Exception as e:
				log("ERROR : " + str(e))
		

	def stop( self, completeCallback = None) :
		old_port = self._server_port
		try:
			proc = self._server_proc

			if proc is not None :
				self._server_proc = None
				del self._server_proc
				if self._use_wrapper:
					proc.stdin.write("x")
					time.sleep(0.2)
				else:
					proc.terminate()
					time.sleep(0.2)
				proc.kill()
				proc.wait()
				proc = None
				del proc
				# running the process on the same port causes zombie processes
				# increment the server port to avoid this
				self._server_port = self._server_port + 1
			
			
			
		except:
			self._server_proc = None
		
		if completeCallback != None:
			hxpanel.default_panel().writeln("stopping server on port: " + str(old_port))
			completeCallback()

	def __del__(self):
		self.stop()
		
		
