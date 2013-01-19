import sys
import os

import haxe.panel as hxpanel

from startup import STARTUP_INFO
from subprocess import Popen, PIPE

import sublime

import thread

def log (msg):
	print msg

def run_cmd_async(args, callback, input=None, cwd=None, env=None):

	def in_thread ():
		out, err = run_cmd(args, input, cwd, env)
		sublime.set_timeout(lambda : callback(out, err), 10)

	thread.start_new_thread(in_thread, ())

def run_cmd( args, input=None, cwd=None, env=None ):
	
	if (cwd == None): 
		cwd = "."

	try: 
		
		if (env == None):
			env = os.environ.copy()


		# do we need this here, or should we take care of this somewhere else
		args = filter(lambda s: s != "", args)
		
		encodedArgs = [a.encode(sys.getfilesystemencoding()) for a in args]
		hxpanel.slide_panel().status("exec: ", " ".join(encodedArgs))
		p = Popen(encodedArgs, cwd=cwd, stdout=PIPE, stderr=PIPE, stdin=PIPE, startupinfo=STARTUP_INFO, env=env)
		


		if isinstance(input, unicode):
			input = input.encode('utf-8')
		out, err = p.communicate(input=input)
		log("runcmd: output:\n" + out.decode('utf-8'))
		
		#print "error: " + err
		return (out.decode('utf-8') if out else '', err.decode('utf-8') if err else '')
	except (OSError, ValueError) as e:
		err = u'Error while running %s: in %s (%s)' % (args[0], cwd, e)
		return ("", err.decode('utf-8'))
