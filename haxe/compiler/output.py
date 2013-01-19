
import haxe.hxtools as hxtools, sublime, re
import haxe.panel as hxpanel

from xml.etree import ElementTree


from elementtree import SimpleXMLTreeBuilder # part of your codebase

ElementTree.XMLTreeBuilder = SimpleXMLTreeBuilder.TreeBuilder





compilerOutput = re.compile("^([^:]+):([0-9]+): characters? ([0-9]+)-?([0-9]+)? : (.*)", re.M)
haxeFileRegex = "^([^:]*):([0-9]+): characters? ([0-9]+)-?[0-9]* :(.*)$"


def get_type_hint (types):
	hints = []
	for i in types :
		hint = i.text.strip()
		
		#print(hint)

		# show complete signature, unless better splitter (-> is not enough) is implemented

		#types = hint.split(" -> ")
		#
		#print(str(types))
#
#				#ret = types.pop()
#				#msg = "";
#				#
#				#if commas >= len(types) :
#				#	if commas == 0 :
#				#		msg = hint + ": No autocompletion available"
#				#		#view.window().run_command("hide_auto_complete")
#				#		#comps.append((")",""))
#				#	else:
#				#		msg =  "Too many arguments."
		#else :
		msg = hint
			#msg = ", ".join(types[commas:]) 

		if msg :
			#msg =  " ( " + " , ".join( types ) + " ) : " + ret + "      " + msg
			hints.append( msg )
	return hints

def collect_completion_fields (li):
	comps = []
	if li is not None : 
		for i in li.getiterator("i"):
			name = i.get("n")
			sig = i.find("t").text
			#doc = i.find("d").text #nothing to do
			insert = name
			hint = name

			if sig is not None :
				types = sig.split(" -> ")
				ret = types.pop()

				if( len(types) > 0 ) :
					#cm = name + "("
					cm = name
					if len(types) == 1 and types[0] == "Void" :
						types = []
						#cm += ")"
						hint = name + "()\t"+ ret
						insert = cm
					else:
						hint = name + "( " + " , ".join( types ) + " )\t" + ret
						if len(hint) > 40: # compact arguments
							hint = hxtools.compactFunc.sub("(...)", hint);
						insert = cm
				else :
					hint = name + "\t" + ret
			else :
				if re.match("^[A-Z]",name ) :
					hint = name + "\tclass"
				else :
					hint = name + "\tpackage"

			#if doc is not None :
			#	hint += "\t" + doc
				#print(doc)
			
			if len(hint) > 40: # compact return type
				m = hxtools.compactProp.search(hint)
				if not m is None:
					hint = hxtools.compactProp.sub(": " + m.group(1), hint)
			
			comps.append( ( hint, insert ) )

	return comps


def extract_errors( str ):
	errors = []
	
	for infos in compilerOutput.findall(str) :
		infos = list(infos)
		f = infos.pop(0)
		l = int( infos.pop(0) )-1
		left = int( infos.pop(0) )
		right = infos.pop(0)
		if right != "" :
			right = int( right )
		else :
			right = left+1
		m = infos.pop(0)

		errors.append({
			"file" : f,
			"line" : l,
			"from" : left,
			"to" : right,
			"message" : m
		}) 

	#print(errors)
	if len(errors) > 0:
		print "should show panel"
		hxpanel.slide_panel().writeln(errors[0]["message"])
		sublime.status_message(errors[0]["message"])

	return errors


def get_completion_output(temp_file, orig_file, output):
	hints, comps = parse_completion_output(temp_file, orig_file, output)
	status, errors = get_completion_status_and_errors(hints, comps, output, temp_file, orig_file)

	return (hints, comps, status, errors)



def parse_completion_output(temp_file, orig_file, output):

	try :
		x = "<root>"+output.encode('utf-8')+"</root>";
		tree = ElementTree.XML(x);
		
	except Exception,e:
		tree = None
		print("invalid xml - error: " + str(e))


	if tree is not None :

		hints = get_type_hint(tree.getiterator("type"))
		comps = collect_completion_fields(tree.find("list"))
	else:
		hints = []
		comps = []

	return (hints, comps)
	

def get_completion_status_and_errors(hints, comps, output, temp_file, orig_file):
	status = ""
	
	errors = []

	if len(hints) > 0 :
		status = " | ".join(hints)

	elif len(hints) == 0 and len(comps) == 0:
		status, errors = parse_completion_errors(output, temp_file, orig_file, status)
		
	
	return status, errors

def parse_completion_errors(output, temp_file, orig_file, status):
	output = output.replace( temp_file , orig_file )
	output = re.sub( u"\(display(.*)\)" ,"",output)
	
	lines = output.split("\n")
	l = lines[0].strip()
	
	if len(l) > 0 :
		if l == "<list>" :
			status = "No autocompletion available"
		elif not re.match( haxeFileRegex , l ):
			status = l
		else :
			status = ""

	#regions = []
	
	# for infos in compilerOutput.findall(err) :
	# 	infos = list(infos)
	# 	f = infos.pop(0)
	# 	l = int( infos.pop(0) )-1
	# 	left = int( infos.pop(0) )
	# 	right = infos.pop(0)
	# 	if right != "" :
	# 		right = int( right )
	# 	else :
	# 		right = left+1
	# 	m = infos.pop(0)

	# 	self.errors.append({
	# 		"file" : f,
	# 		"line" : l,
	# 		"from" : left,
	# 		"to" : right,
	# 		"message" : m
	# 	})
		
	# 	if( f == fn ):
	# 		status = m
		
	# 	if not autocomplete :
	# 		w = view.window()
	# 		if not w is None :
	# 			w.open_file(f+":"+str(l)+":"+str(right) , sublime.ENCODED_POSITION  )
	# 	#if not autocomplete

	errors = extract_errors( output )

	return (status,errors)