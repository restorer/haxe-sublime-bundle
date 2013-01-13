import sublime, sublime_plugin
import time

import os

import re

import haxe.settings as hxsettings
import haxe.completion_server
import haxe.typegen
import haxe.build as hxbuild
import haxe.lib as hxlib
import haxe.commands
import haxe.output_panel

import haxe.compiler.outputparser as outputparser

from haxe.config import Config



import haxe.types as hxtypes

import thread

import haxe.project as hxproject
import haxe.hxtools as hxsourcetools

from haxe.tools import ViewTools, ScopeTools

import haxe.temp as temp
    
from xml.etree import ElementTree


from elementtree import SimpleXMLTreeBuilder # part of your codebase

ElementTree.XMLTreeBuilder = SimpleXMLTreeBuilder.TreeBuilder


def log (msg):
	print msg

def panel () : 
	return haxe.output_panel.HaxePanel

def HaxeCreateType (): 
	return haxe.typegen.HaxeCreateType


haxeFileRegex = "^([^:]*):([0-9]+): characters? ([0-9]+)-?[0-9]* :(.*)$"
controlStruct = re.compile( "\s*(if|switch|for|while)\($" );


bundleFile = __file__
bundlePath = os.path.abspath(bundleFile)
bundleDir = os.path.dirname(bundlePath)

class CompletionContext:
	def __init__(self):
		
		self.completion_running = {}
		self.manual_completion = {}	
		self.current_completion_id = None	
		self.errors = []
	 	self.delayed_completions = {}
		self.currentCompletion = {
			"input" : None,
			"output" : None
		}


	def clear_completion (self):
		self.currentCompletion = {
				"inp" : None,
				"outp" : None
		}

	def set_errors (self, errors):
		self.errors = errors
		
	def __del__(self) :
		print "kill server"
		hxproject.ctx().server.stop_server()

_ctx = None




def ctx():
	global _ctx
	if _ctx is None:
		_ctx = CompletionContext()
	return _ctx



def filter_top_level_completions (offsetChar, all_comps):
	print("number of top level completions all:" + str(len(all_comps)))
		
	comps = []

	isLower = offsetChar in "abcdefghijklmnopqrstuvwxyz"
	isUpper = offsetChar in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
	isDigit = offsetChar in "0123456789"
	isSpecial = offsetChar in "$_"
	offsetUpper = offsetChar.upper()
	offsetLower = offsetChar.lower()
	if isLower or isUpper or isDigit or isSpecial:
		print "its in"
		
		for c in all_comps:
			id = c[1]

			if (offsetChar in id
				or (isUpper and offsetLower in id)
				or (isLower and offsetUpper in id)):
				comps.append(c)
		
	else:
		comps = all_comps


	print "number of top level completions filtered" + str(len(comps))
	return comps

def hx_query_completion(completion_id, last_completion_id, view, offset, build, cache, macroCompletion ):
	

	manual_completion = is_manual_completion(view)

	if manual_completion:
		log("this is manual completion")
		delete_manual_completion(view)

	if (hxsettings.HaxeSettings.no_fuzzy_completion() and not manual_completion):
		trigger_manual_completion(view)
		r = cancel_completion(view)
		#log("start manual completion")
		
		return r


		


	src = ViewTools.get_content(view)
	orig_file = view.file_name()
	src_dir = os.path.dirname(orig_file)
	
	

	#find actual autocompletable char.
	prev = src[offset-1]
	
	commas, completeOffset, toplevelComplete = get_completion_info(view, offset, src, prev)
	
	temp_path, temp_file = temp.create_temp_path_and_file(build, orig_file, src)

	if temp_path is None or temp_file is None:
		# this should never happen, todo proper error message
		return []

	if last_completion_id in ctx().completion_running:
		o1, id1 = ctx().completion_running[last_completion_id]
		if (o1 == completeOffset and id1 == view.id()):
			print "cancel completion, same is running"
			return cancel_completion(view, False)

	top_level_build = build.copy()
	build.add_classpath(temp_path)

	completeChar = src[completeOffset-1]
	inControlStruct = controlStruct.search( src[0:completeOffset] ) is not None

	on_demand = hxsettings.HaxeSettings.top_level_completions_on_demand()

	toplevelComplete = (toplevelComplete or completeChar in ":(," or inControlStruct) and not on_demand

	

	offsetChar = src[offset]
	

	if (offsetChar == "\n" and prev == "." and src[offset-2] == "." and src[offset-3] != "."):
		return [(".\tint iterator", "..")]

	comps = []

	if toplevelComplete :

		all_comps = get_toplevel_completion( src , src_dir , top_level_build )
		comps = filter_top_level_completions(offsetChar, all_comps)
		
	else:
		print "comps_from_not_top_level"
		comps = []
	
	

	if toplevelComplete and (inControlStruct or completeChar not in "(,")  :
		print "comps_from_not_top_level_and_control_struct"
		return comps


	delayed = hxsettings.HaxeSettings.is_delayed_completion()

	display = temp_file + "@" + str(offset)
	
	comps1 = []
	status = ""

	offset = completeOffset

	current_input = create_completion_input_key(orig_file, offset, commas, src, macroCompletion, completeChar)

	def run_compiler_completion ():
		return get_compiler_completion( build, view, display, temp_file, orig_file , macroCompletion )

	last_input = cache["input"]



	print "DELAYED COMPLETION: " + str(delayed)

	use_cache = use_completion_cache(last_input, current_input)

	if use_cache :
		print "comps_from_cache"
		ret, comps1, status = cache["output"]
	else :

		if supported_compiler_completion_char(completeChar): 

			if delayed:
				background_completion(completion_id, list(comps), temp_file, orig_file,temp_path,
					view, handle_completion_output, run_compiler_completion, cache,
					current_input, completeOffset)
				
				ret, comps1, status = "", [], ""
			else:
				ret, err = run_compiler_completion()
				comps1, status = handle_completion_output(temp_file, orig_file, view, err)
		else:
			ret, comps1, status = "",[], ""

	if not use_cache:
		comps.extend(comps1)
	else:
		comps = comps1
	
	if use_cache or not delayed:
		temp.remove_path(temp_path)
		
		cache["output"] = (ret,comps1,status)
		cache["input"] = current_input
	
	panel().status( "haxe-status" , status )

	
	if not use_cache and delayed and hxsettings.HaxeSettings.only_delayed_completions():
		print "empty completion"
		#return [("... ...", " ")]
		return cancel_completion(view, True)
		
	if len(comps) == 0 and hxsettings.HaxeSettings.no_fuzzy_completion():
		return cancel_completion(view)

	return comps

def background_completion(completion_id, basic_comps, temp_file, orig_file, temp_path, 
		view, handle_completion_output, run_compiler_completion,
		cache, current_input, completeOffset):
	hide_delay, show_delay = hxsettings.HaxeSettings.get_completion_delays()

	
	view_id = view.id()
	
	comps = list(basic_comps) # make copy

	only_delayed = hxsettings.HaxeSettings.only_delayed_completions()

	def in_main (ret_, err_):

		comps_, status_ = handle_completion_output(temp_file, orig_file, view, err_)
		
		print "do remove temp_path"
		temp.remove_path(temp_path)
		comps.extend(comps_)

		
		if completion_id == ctx().current_completion_id:
			cache["output"] = (ret_,comps,status_)
			cache["input"] = current_input
		else:
			print "ignored completion"
		
		# do we still need this completion, or is it old
		has_new_comps = len(comps) > len(basic_comps)
		if completion_id == ctx().current_completion_id and (has_new_comps or hxsettings.HaxeSettings.only_delayed_completions()):
			now = time.time()
			ctx().delayed_completions[view_id] = (comps, now)
			if only_delayed:
				print "trigger_auto_complete"
				view.run_command('auto_complete', {'disable_auto_insert': True})
			else:
				view.run_command('hide_auto_complete')
				print "trigger_auto_complete"
				sublime.set_timeout(lambda : view.run_command('auto_complete', {'disable_auto_insert': True}), show_delay)
		else:
			log("ignore background completion")
		
		del ctx().completion_running[completion_id]
	def in_thread():
		ret_, err_ = run_compiler_completion()

		# replace current completion workaround
		# delays are customizable with project settings
		
		sublime.set_timeout(lambda : in_main(ret_, err_), hide_delay if not only_delayed else 20)

	ctx().completion_running[completion_id] = (completeOffset, view.id())
	ctx().current_completion_id = completion_id
	thread.start_new_thread(in_thread, ())	

def create_completion_input_key (fn, offset, commas, src, macro_completion, complete_char):
	return (fn,offset,commas,src[0:offset-1], macro_completion, complete_char)


def use_completion_cache (last_input, current_input):
	return last_input is not None and current_input == last_input

def supported_compiler_completion_char (char):
	return char in "(.,"








def get_toplevel_completion( src , src_dir , build ) :
	cl = []
	packs = []
	stdPackages = []

	comps = [("trace\ttoplevel","trace"),("this\ttoplevel","this"),("super\ttoplevel","super"),("else\ttoplevel","else")]

	src = hxsourcetools.comments.sub("",src)

	localTypes = hxsourcetools.typeDecl.findall( src )
	for t in localTypes :
		if t[1] not in cl:
			print "local" + str(t[1])
			cl.append( t[1] )


	packageClasses, subPacks = hxtypes.extract_types( src_dir, hxproject.ctx().stdClasses, hxproject.ctx().stdPackages )
	for c in packageClasses :
		if c not in cl:
			print "package" + str(c)
			cl.append( c )

	imports = hxsourcetools.importLine.findall( src )
	imported = []
	for i in imports :
		imp = i[1]
		imported.append(imp)
		#dot = imp.rfind(".")+1
		#clname = imp[dot:]
		#cl.append( clname )
		#print( i )

	#print cl

	print str(build.classpaths)

	buildClasses , buildPacks = build.get_types()



	# filter duplicates
	def filter_build (x):
		for c in cl:
			if x == c:
				return False
		return True

	buildClasses = filter(filter_build, buildClasses)
	

	tarPkg = None
	

	if build.target is not None :
		tarPkg = build.target
		if tarPkg == "swf9" :
			tarPkg = "flash"
		if tarPkg == "swf" :
			tarPkg = "flash"

	if build.nmml is not None :
		tarPkg = "flash"
	
	#for c in HaxeComplete.stdClasses :
	#	p = c.split(".")[0]
	#	if tarPkg is None or (p not in targetPackages) or (p == tarPkg) :
	#		cl.append(c)

	

	cl.extend( hxproject.ctx().stdClasses )
	
	cl.extend( buildClasses )
	
	cl.sort();


	
	#print("target : "+build.target)
	for p in hxproject.ctx().stdPackages :
		#print(p)
		if p == "flash9" or p == "flash8" :
			p = "flash"
	#	if tarPkg is None or (p not in targetPackages) or (p == tarPkg) :
		stdPackages.append(p)

	packs.extend( stdPackages )
	

	for v in hxsourcetools.variables.findall(src) :
		comps.append(( v + "\tvar" , v ))
	
	for f in hxsourcetools.functions.findall(src) :
		if f not in ["new"] :
			comps.append(( f + "\tfunction" , f ))

	
	#TODO can we restrict this to local scope ?
	for paramsText in hxsourcetools.functionParams.findall(src) :
		cleanedParamsText = re.sub(hxsourcetools.paramDefault,"",paramsText)
		paramsList = cleanedParamsText.split(",")
		for param in paramsList:
			a = param.strip();
			if a.startswith("?"):
				a = a[1:]
			
			idx = a.find(":") 
			if idx > -1:
				a = a[0:idx]

			idx = a.find("=")
			if idx > -1:
				a = a[0:idx]
				
			a = a.strip()
			cm = (a + "\tvar", a)
			if cm not in comps:
				comps.append( cm )

	for c in cl :
		spl = c.split(".")
		if spl[0] == "flash9" or spl[0] == "flash8" :
			spl[0] = "flash"

		top = spl[0]
		#print(spl)
		
		clname = spl.pop()
		pack = ".".join(spl)
		display = clname

		#if pack in imported:
		#	pack = ""

		if pack != "" :
			display += "\t" + pack
		else :
			display += "\tclass"
		
		spl.append(clname)
		
		if pack in imported or c in imported :
			cm = ( display , clname )
		else :
			cm = ( display , ".".join(spl) )
		if cm not in comps and tarPkg is None or (top not in Config.targetPackages) or (top == tarPkg) : #( build.target is None or (top not in HaxeBuild.targets) or (top == build.target) ) :
			comps.append( cm )
	
	for p in packs :
		cm = (p + "\tpackage",p)
		if cm not in comps :
			comps.append(cm)

	
	return comps

def get_hxsl_completions( view , offset ) :
	comps = []
	for t in ["Float","Float2","Float3","Float4","Matrix","M44","M33","M34","M43","Texture","CubeTexture","Int","Color","include"] :
		comps.append( ( t , "hxsl Type" ) )
	return comps

def get_hxml_completions( view , offset ) :
	src = view.substr(sublime.Region(0, offset))
	currentLine = src[src.rfind("\n")+1:offset]
	m = libFlag.match( currentLine )
	if m is not None :
		return hxlib.HaxeLib.get_completions()
	else :
		return []









def highlight_errors( errors , view ) :
	print "highlight_errors" + str(len(errors))
	fn = view.file_name()
	regions = []
	


	for e in errors :
		if fn.endswith(e["file"]) :
			l = e["line"]
			left = e["from"]
			right = e["to"]
			a = view.text_point(l,left)
			b = view.text_point(l,right)

			regions.append( sublime.Region(a,b))

			view.set_status("haxe-status" , "Error: " + e["message"] )
			panel().status( "haxe-status" , "Error: " + e["message"] )
			
	view.add_regions("haxe-error" , regions , "invalid" , "dot" )

def handle_completion_error(err, temp_file, orig_file, status):
	err = err.replace( temp_file , orig_file )
	err = re.sub( u"\(display(.*)\)" ,"",err)
	
	lines = err.split("\n")
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

	errors = outputparser.extract_errors( err )

	return (status,errors)
	#


def count_commas_and_complete_offset (src, prevComa, completeOffset):
	commas = 0;
	closedPars = 0
	closedBrackets = 0

	for i in range( prevComa , 0 , -1 ) :
		c = src[i]
		if c == ")" :
			closedPars += 1
		elif c == "(" :
			if closedPars < 1 :
				completeOffset = i+1
				break
			else :
				closedPars -= 1
		elif c == "," :
			if closedPars == 0 :
				commas += 1
		elif c == "{" : # TODO : check for { ... , ... , ... } to have the right comma count
			commas = 0
			closedBrackets -= 1
		elif c == "}" :
			closedBrackets += 1

	return (commas, completeOffset)

def get_completion_info (view, offset, src, prev):
	commas = 0
	toplevelComplete = False
	completeOffset = offset
	if prev not in "(." :
		fragment = view.substr(sublime.Region(0,offset))
		prevDot = fragment.rfind(".")
		prevPar = fragment.rfind("(")
		prevComa = fragment.rfind(",")
		prevColon = fragment.rfind(":")
		prevBrace = fragment.rfind("{")
		prevSymbol = max(prevDot,prevPar,prevComa,prevBrace,prevColon)
		
		if prevSymbol == prevComa:
			commas, completeOffset = count_commas_and_complete_offset(src, prevComa, completeOffset)
			#print("closedBrackets : " + str(closedBrackets))
			
		else :

			completeOffset = max( prevDot + 1, prevPar + 1 , prevColon + 1 )
			skipped = src[completeOffset:offset]
			toplevelComplete = hxsourcetools.skippable.search( skipped ) is None and hxsourcetools.inAnonymous.search( skipped ) is None

	return (commas, completeOffset, toplevelComplete)


def run_nme( view, build ) :

	cmd = [ hxsettings.HaxeSettings.haxeLibExec(), "run", "nme", hxbuild.HaxeBuild.nme_target[2], os.path.basename(build.nmml) ]
	target = hxbuild.HaxeBuild.nme_target[1].split(" ")
	cmd.extend(target)
	cmd.append("-debug")

	view.window().run_command("exec", {
		"cmd": cmd,
		"working_dir": os.path.dirname(build.nmml),
		"file_regex": "^([^:]*):([0-9]+): characters [0-9]+-([0-9]+) :.*$"
	})
	return ("" , [], "" )




#class PanelHelper ():
#
#	def __init__ (self):
#		self.panel = None
#
#
#	def clear_output_panel(self, view) :
#		win = view.window()
#
#		self.panel = win.get_output_panel("haxe")
#
#	def panel_output( self , view , text , scope = None ) :
#		win = view.window()
#		if self.panel is None :
#			self.panel = win.get_output_panel("haxe")
#
#		panel = self.panel
#
#		text = datetime.now().strftime("%H:%M:%S") + " " + text;
#		
#		edit = panel.begin_edit()
#		region = sublime.Region(panel.size(),panel.size() + len(text))
#		panel.insert(edit, panel.size(), text + "\n")
#		panel.end_edit( edit )
#
#		if scope is not None :
#			icon = "dot"
#			key = "haxe-" + scope
#			regions = panel.get_regions( key );
#			regions.append(region)
#			panel.add_regions( key , regions , scope , icon )
#		#print( err )
#		win.run_command("show_panel",{"panel":"output.haxe"})
#
#		return self.panel

def is_delayed_completion(view):
	id = view.id() 
	now = time.time()
	delayed = False
	
	if id in ctx().delayed_completions:
		oldTime = ctx().delayed_completions[id][1]
		
		print "check times"
		if (now - oldTime) < 1000:
			delayed = True

	print "is delayed:" + str(delayed)
	return delayed

def cancel_completion(view, hide_complete = True):
	if hide_complete:
		# this seems to work fine, it cancels the current
		# triggered completion without poping up a completion
		# view
		view.run_command('hide_auto_complete')
	return [("  ...  ", "")]

def trigger_manual_completion(view):
	id = view.id()
	now = time.time()
	ctx().manual_completion[id] = ("", now)

	def run_complete():
		log("trigger auto_complete")
		view.run_command("auto_complete" , {
			"api_completions_only" : True,
			"disable_auto_insert" : True,
			"next_completion_if_showing" : False,
			"args" : { "supi" : 5}
		})

	sublime.set_timeout(run_complete, 20)
	
def delete_manual_completion(view):
	id = view.id() 
	if id in ctx().manual_completion:
		del ctx().manual_completion[id]

def is_manual_completion(view):
	id = view.id() 
	now = time.time()
	manual = False
	
	if id in ctx().manual_completion:
		oldTime = ctx().manual_completion[id][1]
		
		
		if (now - oldTime) < 1000:
			manual = True

	print "is manual:" + str(manual)
	return manual


def is_macro_completion (view):
	id = view.id() 
	now = time.time()
	macroComp = False
	if id in haxe.commands.HaxeDisplayMacroCompletion.completions:
		oldTime = haxe.commands.HaxeDisplayMacroCompletion.completions[id]
		del haxe.commands.HaxeDisplayMacroCompletion.completions[id]

		if (now - oldTime) < 500:
			#print "do macro completion"
			macroComp = True
	return macroComp


	

def hxsl_query_completion(view, offset):
	return get_hxsl_completions( view , offset )
def hxml_query_completion(view, offset):
	return get_hxml_completions( view , offset )

def get_compiler_completion( build, view , display, temp_file, orig_file, macroCompletion = False ) :
		
	serverMode = hxproject.ctx().is_server_mode()
	

	ctx().set_errors([])

	build.set_auto_completion(display, macroCompletion)
	
	if hxsettings.HaxeSettings.showCompletionTimes(view):
		build.set_times()



	build.set_build_cwd()


	haxeExec = hxsettings.HaxeSettings.haxeExec(view)

	return build.run(haxeExec, serverMode, view, hxproject.ctx().server)




def handle_completion_output(temp_file, orig_file, view, err):

	try :
		x = "<root>"+err.encode('utf-8')+"</root>";
		tree = ElementTree.XML(x);
		
	except Exception,e:
		tree = None
		print("invalid xml - error: " + str(e))


	if tree is not None :

		hints = outputparser.get_type_hint(tree.getiterator("type"))
		comps = outputparser.collect_completion_fields(tree.find("list"))
	else:
		hints = []
		comps = []

	status = ""
	
	if len(hints) > 0 :
		status = " | ".join(hints)

	elif len(hints) == 0 and len(comps) == 0:
		status, errors = handle_completion_error(err, temp_file, orig_file, status)
		ctx().set_errors(errors)
		highlight_errors( errors, view )
	

	return ( comps, status )

class HaxeComplete( sublime_plugin.EventListener ):

	def on_load( self, view ) :

		
		if view is None or view.file_name() is None or ViewTools.is_unsupported(view): 
			return
		
		hxproject.generate_build( view )
		highlight_errors( ctx().errors, view )


	def on_post_save( self , view ) :
		if ViewTools.is_hxml(view):
			hxproject.clear_build()
			ctx().clear_completion()

	# view is None then it's a preview
	def on_activated( self , view ) :
		
		if view is None or view.file_name() is None or ViewTools.is_unsupported(view): 
			return
		
		hxproject.get_build(view)
		hxproject.extract_build_args( view )
		
		hxproject.generate_build(view)
		highlight_errors( ctx().errors, view )

	def on_pre_save( self , view ) :

		if not ViewTools.is_haxe(view) :
			return []

		ViewTools.create_missing_folders(view)
		


	def on_query_completions(self, view, prefix, locations):

		start_time = time.time()

		completion_id = start_time
		last_completion_id = ctx().current_completion_id
		
		pos = locations[0]
		
		offset = pos - len(prefix)

		comps =  []

		if offset == 0 : 
			return comps 
		
		scopes = ViewTools.get_scopes_at(view, pos)

		if (ScopeTools.contains_string_or_comment(scopes)):
			return comps

		if Config.SOURCE_HXML in scopes:
			comps = hxml_query_completion( view , offset )
		
		if Config.SOURCE_HAXE in scopes :
			if ViewTools.is_hxsl(view) :
				comps = hxsl_query_completion( view , offset )
			else : 

				if is_delayed_completion(view):
					c = ctx().delayed_completions[view.id()][0]
					del ctx().delayed_completions[view.id()]
					comps = c

				else:
					# get build and maybe use cache
					build = hxproject.get_build( view ).copy()
					cache = ctx().currentCompletion
					

					macro_completion = is_macro_completion(view)
					comps = hx_query_completion(completion_id, last_completion_id, view, offset, build, cache, macro_completion)
				
		end_time = time.time()
		log("on_query_completion time: " + str(end_time-start_time))
		log("number of completions: " + str(len(comps)))
		return comps
	

	# def on_modified( self , view ):
	# 	print "on_modified"
	# 	win = sublime.active_window()
	# 	if win is None :
	# 		return None

	# 	isOk = ( win.active_view().buffer_id() == view.buffer_id() )
	# 	if not isOk :
	# 		return None
		
	# 	sel = view.sel()
	# 	caret = 0
	# 	for s in sel :
	# 		caret = s.a
		
	# 	if caret == 0 or not CaretTools.in_haxe_code(view, caret):
	# 		return None

	# 	src = view.substr(sublime.Region(0, view.size()))
	# 	ch = src[caret-1]
	# 	#print(ch)
	# 	if ch not in ".(:, " :
	# 		#print("here")
	# 		print "on modified run completion"
	# 		view.run_command("haxe_display_completion")
	# 	#else :
	# 	#	view.run_command("haxe_insert_completion")



	#def run_build( self , view ) :
	#	print "run build"
	#	err, comps, status = self.get_compiler_completion( view )
	#	view.set_status( "haxe-status" , status )
	#	panel().status( "haxe-status" , status )
	#	print status


#sublime.set_timeout(HaxeLib.scan, 200)