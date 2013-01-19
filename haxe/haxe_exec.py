import sys
import sublime
import os


import haxe.panel as hxpanel


from startup import STARTUP_INFO
from subprocess import Popen, PIPE


stexec = __import__("exec") 


def runcmd( args, input=None, cwd=None, env=None ):
	
	if (cwd == None): 
		cwd = "."

	try: 
		
		if (env == None):
			env = os.environ.copy()

		args = filter(lambda s: s != "", args)
		

		
		#print sys.getfilesystemencoding()
		#p = Popen(,  stdout=PIPE, stderr=PIPE, stdin=PIPE, startupinfo=STARTUP_INFO, env=env)

		encodedArgs = [a.encode(sys.getfilesystemencoding()) for a in args]
		print " ".join(encodedArgs)
		p = Popen(encodedArgs, cwd=cwd, stdout=PIPE, stderr=PIPE, stdin=PIPE, startupinfo=STARTUP_INFO, env=env)
		


		if isinstance(input, unicode):
			input = input.encode('utf-8')
		out, err = p.communicate(input=input)
		print "runcmd: output:\n" + out.decode('utf-8')
		
		#print "error: " + err
		return (out.decode('utf-8') if out else '', err.decode('utf-8') if err else '')
	except (OSError, ValueError) as e:
		err = u'Error while running %s: in %s (%s)' % (args[0], cwd, e)
		return ("", err.decode('utf-8'))
