import sublime
import re
import os

from haxe import panel as hxpanel
from haxe import settings as hxsettings

from haxe.tools import hxsrctools

from haxe.log import log

from haxe.plugin import is_st2, is_st3

from xml.etree import ElementTree
from xml.etree.ElementTree import XMLTreeBuilder

if is_st2:
	from elementtree import SimpleXMLTreeBuilder # part of your codebase
	ElementTree.XMLTreeBuilder = SimpleXMLTreeBuilder.TreeBuilder

compiler_output = re.compile("^([^:]+):([0-9]+): (?:character(?:s?)|line(?:s?))? ([0-9]+)-?([0-9]+)? : (.*)", re.M)

no_classes_found = re.compile("^No classes found in .*", re.M)

no_classes_found_in_trace = re.compile("^No classes found in trace$", re.M)

haxe_compiler_line = "^([^:]*):([0-9]+): characters? ([0-9]+)-?[0-9]* :(.*)$"



class CompletionEntry:
	def __init__(self, hint, insert, doc):
		self.hint = hint
		self.insert = insert
		self.doc = doc

def get_type_hint (types):
	hints = []
	for i in types :
		hint = i.text.strip()
		hint_types = hxsrctools.split_function_signature(hint)
		hints.append( hint_types )
	return hints


type_parameter_name = re.compile("^([A-Z][_a-zA-Z0-9]*)")

def get_function_type_params(name, signature_types):

	new_args = []
	type_params = dict()
	name_len = len(name)
	for t in signature_types:
		new_args.append("".join(t.split(name + ".")))
		while True:
			index = t.find(name)
			if index == -1:
				break
			type_start_index = index + name_len + 1
			t = t[type_start_index:]
			m = type_parameter_name.match(t)
			if m != None:
				param_name = m.group(1)
				type_params[param_name] = True
			else:
				break

	type_param_list = list(reversed(list(type_params.keys())))
	return new_args, type_param_list


def completion_field_to_entry(name, sig, doc):
	insert = name
	label = name
	
	smart_snippets = hxsettings.smart_snippets_on_completion()
	not_smart = not smart_snippets

	if sig is not None :
		types = hxsrctools.split_function_signature(sig) 
		
		types, type_params = get_function_type_params(name, types)

		params_sig = ""

		if len(type_params) > 0:
			params_sig = "<" + ", ".join(type_params) + ">"


		log(str(types))
		log(str(type_params))
		
		
		ret = types.pop()

		signature_separator = " : " if is_st3 else "\t"

		if( len(types) > 0 ) :
			
			if len(types) == 1 and types[0] == "Void" :

				label = (name + params_sig + "()" + signature_separator + ret) if not_smart else (name + "()" + signature_separator+ ret)
				insert = name if not_smart else "" + name + "${1:()}"
			else:
				def escape_type (x):
					return x.replace("}", "\}").replace("{", "\{")

				params = "( " + ", ".join( types ) + " )"
				label = name + params_sig + params + signature_separator + ret
				
				hint_to_long = is_st2 and len(label) > 40

				if hint_to_long: # compact arguments
					label = hxsrctools.compact_func.sub("(...)", label);
				
				new_types = list(types)
				for i in range(0, len(new_types)):
					new_types[i] = "${" + str(i+2) + ":" + escape_type(new_types[i]) + "}"

				insert = name if not_smart else name + "${1:( " + ", ".join( new_types ) + " )}"
		else :
			label = name + params_sig + signature_separator + ret
	else :
		label = name + "\tclass" if re.match("^[A-Z]",name ) else name + "\tpackage"
			
	
	if is_st2 and len(label) > 40: # compact return type
		m = hxsrctools.compact_prop.search(label)
		if m is not None:
			label = hxsrctools.compact_prop.sub(": " + m.group(1), label)
	
	res = CompletionEntry( label, insert, doc )

	return res
		

def collect_completion_fields (li):
	comps = []
	if li is not None : 
		for i in li.getiterator("i"):
			name = i.get("n")
			sig = i.find("t").text
			doc = i.find("d").text #nothing to do
			entry = completion_field_to_entry(name, sig, doc)
			
			comps.append(entry)

	return comps


def extract_errors( str ):
	errors = []
	
	#log("error_str: |||" + str + "|||")
	# swallow no classes found in * errors where * could be trace or an unknown variable etc.
	if len(no_classes_found.findall(str)) > 0:
		#log("just no classes found error")
		errors = []
	else:
		for infos in compiler_output.findall(str) :
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

			if m != "Unexpected |":
				errors.append({
					"file" : f,
					"line" : l,
					"from" : left,
					"to" : right,
					"message" : m
				}) 

	
		#errors.append({ "file:" : "", "line" : 0, "from" : 0, "to" : 0, "message" : "".join(str.split("\n")) + " ( are you referencing a variable that doesn't exist?)"})
	#print(errors)
	if len(errors) > 0:
		log("should show panel")
		hxpanel.slide_panel().writeln(errors[0]["message"])
		sublime.status_message(errors[0]["message"])

	return errors


def get_completion_output(temp_file, orig_file, output, commas):
	hints, comps = parse_completion_output(temp_file, orig_file, output)

	new_hints = []
	for h in hints:
		if len(h) > commas:
			new_hints.append(h[commas:])
	hints = new_hints

	status, errors = get_completion_status_and_errors(hints, comps, output, temp_file, orig_file)

	return (hints, comps, status, errors)

def parse_completion_output(temp_file, orig_file, output):

	try :
		if is_st3:
			x = "<root>"+output+"</root>";
		else:
			x = "<root>"+output.encode('utf-8')+"</root>";
		tree = ElementTree.XML(x);
		
	except Exception as e:
		tree = None
		log("invalid xml - error: " + str(e))


	if tree is not None :

		hints = get_type_hint(tree.getiterator("type"))
		comps = collect_completion_fields(tree.find("list"))
		log("hints:" + str(hints))
		log("comps:" + str(comps))
	else:
		hints = []
		comps = []
		
	if len(re.findall(no_classes_found_in_trace, output)) > 0:
		smart_snippets = hxsettings.smart_snippets_on_completion()
		if smart_snippets:
			insert = "${1:value:Dynamic}"
		else:
			insert = "${0}"
		comps.append(CompletionEntry("value:Dynamic", insert, ""))

	return (hints, comps)
	

def get_completion_status_and_errors(hints, comps, output, temp_file, orig_file):
	status = ""
	
	errors = []

	if len(hints) == 0 and len(comps) == 0:
		status, errors = parse_completion_errors(output, temp_file, orig_file, status)
		
	return status, errors

def parse_completion_errors(output, temp_file, orig_file, status):
	log("output:" + output)
	log("status:" + status)
	log("orig_file:" + orig_file)
	log("temp_file:" + temp_file)

	# get rid of slashes in paths inside of error messages on windows
	# to replace temp_file with orig_file afterwards
	sep = os.sep
	log("sep: " + sep)
	if sep == "\\":
		def slash_replace(match_obj):
			log("matched")
			return sep.join(match_obj.group(0).split("/"))

		output = re.sub(u"[A-Za-z]:(.*)[.]hx", slash_replace, output);

	output = output.replace( temp_file , orig_file )
	
	log("output after replace: " + output)
	output = re.sub( u"\(display(.*)\)" ,"",output)
	
	lines = output.split("\n")
	l = lines[0].strip()
	
	if len(l) > 0 :
		if l == "<list>" :
			status = "No autocompletion available"
		elif not re.match( haxe_compiler_line , l ):
			status = l
			log(l)
		else :
			status = ""

	errors = extract_errors( output )
	

	return (status,errors)