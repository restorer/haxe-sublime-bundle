import sys
import os
import sublime
import thread

from startup import STARTUP_INFO
from subprocess import Popen, PIPE


def run_cmd_async(args, callback, input=None, cwd=None, env=None):

	def in_thread ():
		out, err = run_cmd(args, input, cwd, env)
		sublime.set_timeout(lambda : callback(out, err), 10)

	thread.start_new_thread(in_thread, ())

def _decoded(x):
	return x.decode('utf-8') if x else ''

def run_cmd( args, input=None, cwd=None, env=None ):
	
	if cwd == None: 
		cwd = "."

	try: 
		base_env =os.environ.copy() 
		# if env == None:
		# 	env = os.environ.copy()
		base_env.update(env)
		env = base_env
		for k in env:
			
			try:
				val = unicode(env[k], "ISO-8859-1").encode(sys.getfilesystemencoding())
			except:
				val = env[k].encode(sys.getfilesystemencoding())
		
			env[k] = os.path.expandvars(val)




		# safely remove empty strings from args
		args = filter(lambda s: s != "", args)
		
		def encode_arg(a):
			try:
				a = unicode(a, "ISO-8859-1").encode(sys.getfilesystemencoding())
			except:
				a = a.encode(sys.getfilesystemencoding())
			return a

		encoded_args = [encode_arg(a) for a in args]

		p = Popen(encoded_args, cwd=cwd, stdout=PIPE, stderr=PIPE, stdin=PIPE, 
				startupinfo=STARTUP_INFO, env=env)
		
		if isinstance(input, unicode):
			input = input.encode('utf-8')
		out, err = p.communicate(input=input)

		return _decoded(out), _decoded(err)

	except (OSError, ValueError) as e:
		err = u'Error while running %s: in %s (%s)' % (args[0], cwd, e)
		return ("", _decoded(err))
