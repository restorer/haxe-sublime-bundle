
import haxe.hxtools as hxtools, sublime, re
import haxe.output_panel

def panel () : 
	return haxe.output_panel.HaxePanel

compilerOutput = re.compile("^([^:]+):([0-9]+): characters? ([0-9]+)-?([0-9]+)? : (.*)", re.M)



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
		panel().writeln(errors[0]["message"])
		sublime.status_message(errors[0]["message"])

	return errors