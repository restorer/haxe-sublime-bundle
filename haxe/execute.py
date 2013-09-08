import sys
import os
import sublime

from subprocess import Popen, PIPE

from haxe.plugin import STARTUP_INFO

from haxe.plugin import is_st3

from haxe.tools.stringtools import encode_utf8

from haxe.log import log

if is_st3:
	import _thread as thread
else:
	import thread

def run_cmd_async(args, callback, input=None, cwd=None, env=None):

	def in_thread ():
		out, err = run_cmd(args, input, cwd, env)
		
		sublime.set_timeout(lambda : callback(out, err), 1)

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
		if env is not None:
			base_env.update(env)
		env = base_env
		for k in env:
			
			try:
				if is_st3:
					val = env[k] # unicode(env[k], "ISO-8859-1")
				else:
					val = unicode(env[k], "ISO-8859-1").encode(sys.getfilesystemencoding())
			except:
				if is_st3:
					val = env[k]
				else:
					val = env[k].encode(sys.getfilesystemencoding())
		
			env[k] = os.path.expandvars(val)


		# safely remove empty strings from args
		args = list(filter(lambda s: s != "", args))
		
		def encode_arg(a):
			try:
				if is_st3:
					pass
					#a = unicode(a, "ISO-8859-1")
				else:
					a = unicode(a, "ISO-8859-1").encode(sys.getfilesystemencoding())
			except:
				a = a.encode(sys.getfilesystemencoding())
			return a
		
		encoded_args = [encode_arg(a) for a in args]
		p = Popen(encoded_args, cwd=cwd, stdout=PIPE, stderr=PIPE, stdin=PIPE, 
				startupinfo=STARTUP_INFO, env=env)
		if not is_st3 and isinstance(input, unicode):
			input = input.encode('utf-8')
		elif is_st3 and isinstance(input, str):
			input = input.encode("utf-8")
		#print("INPUT:" + str(input))
		out, err = p.communicate(input=input)

		return _decoded(out), _decoded(err)

	except (OSError, ValueError) as e:
		err = u'Error while running %s: in %s (%s)' % (args[0], cwd, e)
		return ("", err)
