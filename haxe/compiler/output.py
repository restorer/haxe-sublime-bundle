
import haxe.hxtools as hxtools, sublime, re
import haxe.panel as hxpanel

import haxe.settings as hxsettings

from xml.etree import ElementTree


from haxe.log import log

from elementtree import SimpleXMLTreeBuilder # part of your codebase

ElementTree.XMLTreeBuilder = SimpleXMLTreeBuilder.TreeBuilder





compilerOutput = re.compile("^([^:]+):([0-9]+): characters? ([0-9]+)-?([0-9]+)? : (.*)", re.M)
haxeFileRegex = "^([^:]*):([0-9]+): characters? ([0-9]+)-?[0-9]* :(.*)$"



def split_signature (signature):
	openP = 0
	openB = 0
	openS = 0

	types = []
	count = len(signature)
	cur = ""
	pos = 0
	while (True):
		if pos > count-1:
			types.append(cur)
			break

		c = signature[pos]
		next = signature[pos+1] if pos < count-1 else None
		

		if (c == "-" and next == ">"):
			if (openP == 0 and openB == 0 and openS == 0):
				types.append(cur)
				cur = ""
			else:
				cur += "->"
			
			pos += 2
		elif (c == " " and openP == 0 and openB == 0 and openS == 0):
			pos += 1
		elif (c == "{"):
			pos += 1
			openB += 1
			cur += c
		elif (c == "}"):
			pos += 1
			openB -= 1
			cur += c
		elif (c == "("):
			pos += 1
			openP += 1
			cur += c
		elif (c == ")"):
			pos += 1
			openP -= 1
			cur += c
		elif (c == "<"):
			pos += 1
			openS += 1
			cur += c
		
		elif (c == ">"):
			pos += 1
			openS -= 1
			cur += c
		else:
			pos += 1
			cur += c
	return types







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
		log("hint: " + msg)
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
			doc = i.find("d").text #nothing to do
			insert = name
			insert_smart = None
			hint = name
			hint_smart = None

			smart_snippets = hxsettings.smart_snippets()
			show_smart = smart_snippets != "none"
			show_hints = smart_snippets != "only"

			smart_id = "-" if show_hints else ""

			if sig is not None :
				types = split_signature(sig) 
				
				def escape_type (x):
					return x.replace("}", "\}").replace("{", "\{")
				
				
				ret = types.pop()

				if( len(types) > 0 ) :
					#cm = name + "("
					cm = name
					if len(types) == 1 and types[0] == "Void" :
						types = []
						#cm += ")"
						hint = name + "()\t"+ ret
						hint_smart = name + smart_id +"()\t"+ ret
						insert = cm
						insert_smart = "" + name + "${1:()}"
					else:
						hint = name + "( " + " , ".join( types ) + " )\t" + ret
						
						hint_smart = "" + name + smart_id +"( " + " , ".join( types ) + " )\t" + ret
						if len(hint) > 40: # compact arguments
							hint = hxtools.compactFunc.sub("(...)", hint);
						if len(hint_smart) > 40: # compact arguments
							hint_smart = hxtools.compactFunc.sub("(...)", hint_smart);
						insert = cm
						new_types = list(types)
						for i in range(0, len(new_types)):
							new_types[i] = "${" + str(i+2) + ":" + escape_type(new_types[i]) + "}"

						insert_smart = name + "${1:( " + " , ".join( new_types ) + " )}"
				else :
					hint = name + "\t" + ret
					
			else :
				if re.match("^[A-Z]",name ) :
					hint = name + "\tclass"
					
				else :
					hint = name + "\tpackage"
					

			#	hint += "\t" + doc
				#print(doc)
			
			# store docs and after selection show them in panel (on_modified)

			
			if len(hint) > 40: # compact return type
				m = hxtools.compactProp.search(hint)
				if not m is None:
					hint = hxtools.compactProp.sub(": " + m.group(1), hint)
			
			if (show_hints or hint_smart == None):
				comps.append( ( hint, insert, doc ) )

			if show_smart and hint_smart != None:
				if len(hint_smart) > 40: # compact return type
					m = hxtools.compactProp.search(hint_smart)
					if not m is None:
						hint_smart = hxtools.compactProp.sub(": " + m.group(1), hint_smart)
				comps.append( ( hint_smart, insert_smart, doc ) )

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
		log("should show panel")
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
		log("invalid xml - error: " + str(e))


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