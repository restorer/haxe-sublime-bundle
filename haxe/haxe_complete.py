import sys
#sys.path.append("/usr/lib/python2.6/")
#sys.path.append("/usr/lib/python2.6/lib-dynload")

import sublime, sublime_plugin
import time
import tempfile
import os
#import xml.parsers.expat
import re
import codecs 
import glob 

import shutil

import haxe.settings
import haxe.completion_server

import haxe.typegen
import haxe.build
import haxe.config
from haxe.config import Config
import haxe.lib
import haxe.commands
import haxe.output_panel

import haxe.project

from haxe.tools import ViewTools, ScopeTools, PathTools

project = sys.modules["haxe.project"]

def panel () : 
	return haxe.output_panel.HaxePanel


def HaxeCreateType (): 
	return haxe.typegen.HaxeCreateType


hxbuild = sys.modules["haxe.build"]
hxsettings =  sys.modules["haxe.settings"]
hxconfig =  sys.modules["haxe.config"]
hxlib =  sys.modules["haxe.lib"]

    
from xml.etree import ElementTree


from elementtree import SimpleXMLTreeBuilder # part of your codebase

ElementTree.XMLTreeBuilder = SimpleXMLTreeBuilder.TreeBuilder


from datetime import datetime


from haxe.haxe_exec import runcmd

compilerOutput = re.compile("^([^:]+):([0-9]+): characters? ([0-9]+)-?([0-9]+)? : (.*)", re.M)
compactFunc = re.compile("\(.*\)")
compactProp = re.compile(":.*\.([a-z_0-9]+)", re.I)
spaceChars = re.compile("\s")
wordChars = re.compile("[a-z0-9._]", re.I)
importLine = re.compile("^([ \t]*)import\s+([a-z0-9._]+);", re.I | re.M)
usingLine = re.compile("^([ \t]*)using\s+([a-z0-9._]+);", re.I | re.M)
packageLine = re.compile("package\s*([a-z0-9.]*);", re.I)
libLine = re.compile("([^:]*):[^\[]*\[(dev\:)?(.*)\]")
classpathLine = re.compile("Classpath : (.*)")
typeDecl = re.compile("(class|typedef|enum|typedef)\s+([A-Z][a-zA-Z0-9_]*)\s*(<[a-zA-Z0-9_,]+>)?" , re.M )
libFlag = re.compile("-lib\s+(.*?)")
skippable = re.compile("^[a-zA-Z0-9_\s]*$")
inAnonymous = re.compile("[{,]\s*([a-zA-Z0-9_\"\']+)\s*:\s*$" , re.M | re.U )
extractTag = re.compile("<([a-z0-9_-]+).*\s(name|main)=\"([a-z0-9_./-]+)\"", re.I)
variables = re.compile("var\s+([^:;\s]*)", re.I)
functions = re.compile("function\s+([^;\.\(\)\s]*)", re.I)
functionParams = re.compile("function\s+[a-zA-Z0-9_]+\s*\(([^\)]*)", re.M)
paramDefault = re.compile("(=\s*\"*[^\"]*\")", re.M)
isType = re.compile("^[A-Z][a-zA-Z0-9_]*$")
comments = re.compile("(//[^\n\r]*?[\n\r]|/\*(.*?)\*/)", re.MULTILINE | re.DOTALL )


haxeVersion = re.compile("haxe_([0-9]{3})",re.M)

haxeFileRegex = "^([^:]*):([0-9]+): characters? ([0-9]+)-?[0-9]* :(.*)$"
controlStruct = re.compile( "\s*(if|switch|for|while)\($" );


bundleFile = __file__
bundlePath = os.path.abspath(bundleFile)
bundleDir = os.path.dirname(bundlePath)




class TempClasspath:

	id = 0

	@staticmethod
	def create_temp_path(build):



		id = TempClasspath.id
		path = build.get_build_folder()

		if path is None:
			print "path of build is None"
			return None


		temp_path = os.path.join(path, "tmp" + str(id))

		while os.path.exists(temp_path):
			id += 1
			temp_path = os.path.join(path, "tmp" + str(id))
		print "tempPath: " + temp_path
		PathTools.removeDir(temp_path)
		os.makedirs(temp_path)
		return temp_path

	@staticmethod
	def create_file(temp_path, build, orig_file, content):
		relative = build.get_relative_path(orig_file)
		print "relative:" + str(relative)
		print "temp_path:" + str(temp_path)
		if relative is None:
			return None
		new_file = os.path.join(temp_path, relative)
		new_file_dir = os.path.dirname(new_file)
		if not os.path.exists(new_file_dir):
			os.makedirs(new_file_dir)
		print "new_file:" + new_file
		f = codecs.open( new_file , "wb" , "utf-8" , "ignore" )
		f.write( content )
		f.close()
		return new_file

	@staticmethod
	def create_temp_path_and_file(build, orig_file, content):
		temp_path = TempClasspath.create_temp_path(build)
		if temp_path is None:
			return None
		print "temp_path:" + str(temp_path)
		temp_file = TempClasspath.create_file(temp_path, build, orig_file, content)
		return temp_path, temp_file

	@staticmethod
	def remove_path (temp_path):
		PathTools.removeDir(temp_path)






class HaxeOutputConverter ():

	@staticmethod
	def get_type_hint (types):
		hints = []
		for i in types :
			hint = i.text.strip()
			
			print(hint)

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

	@staticmethod
	def collect_completion_fields (li):
		comps = []
		if li is not None : 
			for i in li.getiterator("i"):
				name = i.get("n")
				sig = i.find("t").text
				doc = i.find("d").text #nothing to do
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
								hint = compactFunc.sub("(...)", hint);
							insert = cm
					else :
						hint = name + "\t" + ret
				else :
					if re.match("^[A-Z]",name ) :
						hint = name + "\tclass"
					else :
						hint = name + "\tpackage"

				if doc is not None :
				#	hint += "\t" + doc
					print(doc)
				
				if len(hint) > 40: # compact return type
					m = compactProp.search(hint)
					if not m is None:
						hint = compactProp.sub(": " + m.group(1), hint)
				
				comps.append( ( hint, insert ) )

		return comps

	@staticmethod
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



def prepare_build_args_for_completion (serverMode, build, macroCompletion, cwd, showTimes, display):
	
	build = build.copy()

	build.set_auto_completion(display, macroCompletion)

	print "use server mode:" + str(serverMode)

	if serverMode:
		build.set_server_mode(HaxeComplete.instance().server.serverPort)
	
	build.set_cwd(cwd)

	if showTimes:
		build.set_times()

	return build.args

def get_haxe_completions( build, cache , run_haxe, view , offset, macroCompletion = False ):

	print "haxe completion"
	src = ViewTools.get_content(view)
	fn = view.file_name()
	src_dir = os.path.dirname(fn)
	

	#packageMatch = re.match(packageLine, src)

	temp_path, temp_file = TempClasspath.create_temp_path_and_file(build, fn, src)

	build.add_classpath(temp_path)



	print "classpaths:" + str(build.classpaths)
	

	#find actual autocompletable char.
	
	prev = src[offset-1]
	
	comps = []
	#print("prev : "+prev)
	commas, completeOffset, toplevelComplete = get_completion_info(view, offset, src, prev)
	
	completeChar = src[completeOffset-1]
	inControlStruct = controlStruct.search( src[0:completeOffset] ) is not None

	toplevelComplete = toplevelComplete or completeChar in ":(," or inControlStruct

	if toplevelComplete :
		#print("toplevel")
		comps = get_toplevel_completion( src , src_dir , build )
		#print(comps)
	
	offset = completeOffset
	
	#if prev == "." and src[offset-2] in ".1234567890" :
		#comps.append(("... [iterator]",".."))
		#comps.append((".","."))

	if toplevelComplete and (inControlStruct or completeChar not in "(,") :
		return comps



	print "classpaths:" + str(build.classpaths)



	ret, comps1, status = get_haxe_actual_completion_data(cache, build, completeChar, view, macroCompletion, temp_file, offset, commas, src, run_haxe)
	
	TempClasspath.remove_path(temp_path)

	comps.extend(comps1)
	
	panel().status( "haxe-status" , status )



	
	return comps



def extract_types( path , depth = 0 ) :

		classes = []
		packs = []
		hasClasses = False
		
		for fullpath in glob.glob( os.path.join(path,"*.hx") ) : 
			f = os.path.basename(fullpath)

			cl, ext = os.path.splitext( f )
								
			if cl not in HaxeComplete.stdClasses:
				s = codecs.open( os.path.join( path , f ) , "r" , "utf-8" , "ignore" )
				src = comments.sub( "" , s.read() )
				
				clPack = "";
				for ps in packageLine.findall( src ) :
					clPack = ps
				
				if clPack == "" :
					packDepth = 0
				else:
					packDepth = len(clPack.split("."))

				for decl in typeDecl.findall( src ):
					t = decl[1]

					if( packDepth == depth ) : # and t == cl or cl == "StdTypes"
						if t == cl or cl == "StdTypes":
							classes.append( t )
						else: 
							classes.append( cl + "." + t )

						hasClasses = True
		

		if hasClasses or depth == 0 : 
			
			for f in os.listdir( path ) :
				
				cl, ext = os.path.splitext( f )
												
				if os.path.isdir( os.path.join( path , f ) ) and f not in HaxeComplete.stdPackages :
					packs.append( f )
					subclasses,subpacks = extract_types( os.path.join( path , f ) , depth + 1 )
					for cl in subclasses :
						classes.append( f + "." + cl )
					
					
		classes.sort()
		packs.sort()
		return classes, packs


def get_toplevel_completion( src , src_dir , build ) :
	cl = []
	comps = [("trace","trace"),("this","this"),("super","super"),("else","else")]

	src = comments.sub("",src)
	
	localTypes = typeDecl.findall( src )
	for t in localTypes :
		if t[1] not in cl:
			cl.append( t[1] )

	packageClasses, subPacks = extract_types( src_dir )
	for c in packageClasses :
		if c not in cl:
			cl.append( c )

	imports = importLine.findall( src )
	imported = []
	for i in imports :
		imp = i[1]
		imported.append(imp)
		#dot = imp.rfind(".")+1
		#clname = imp[dot:]
		#cl.append( clname )
		#print( i )

	#print cl
	buildClasses , buildPacks = build.get_types()

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

	cl.extend( HaxeComplete.stdClasses )
	cl.extend( buildClasses )
	cl.sort();

	packs = []
	stdPackages = []
	#print("target : "+build.target)
	for p in HaxeComplete.stdPackages :
		#print(p)
		if p == "flash9" or p == "flash8" :
			p = "flash"
	#	if tarPkg is None or (p not in targetPackages) or (p == tarPkg) :
		stdPackages.append(p)

	packs.extend( stdPackages )
	packs.extend( buildPacks )
	packs.sort()

	for v in variables.findall(src) :
		comps.append(( v + "\tvar" , v ))
	
	for f in functions.findall(src) :
		if f not in ["new"] :
			comps.append(( f + "\tfunction" , f ))

	
	#TODO can we restrict this to local scope ?
	for paramsText in functionParams.findall(src) :
		cleanedParamsText = re.sub(paramDefault,"",paramsText)
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
		if cm not in comps and tarPkg is None or (top not in hxconfig.Config.targetPackages) or (top == tarPkg) : #( build.target is None or (top not in HaxeBuild.targets) or (top == build.target) ) :
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

def savetotemp( path, src ):
	f = tempfile.NamedTemporaryFile( delete=False )
	f.write( src )
	return f

def collect_compiler_info ():
	out, err = runcmd( [hxsettings.HaxeSettings.haxeExec(), "-main", "Nothing", "-v", "--no-output"] )
			
	m = classpathLine.match(out)
	
	classes = []
	packs = []
	stdPaths = []

	if m is not None :
		stdPaths = set(m.group(1).split(";")) - set([".","./"])
	
	for p in stdPaths : 
		#print("std path : "+p)
		if len(p) > 1 and os.path.exists(p) and os.path.isdir(p):
			classes, packs = extract_types( p )
			

	ver = re.search( haxeVersion , out )

	return (classes, packs, ver, stdPaths)

def find_hxml( folder ) :
	builds = []
	hxmls = glob.glob( os.path.join( folder , "*.hxml" ) )
	for build in hxmls:

		currentBuild = hxbuild.HaxeBuild()
		currentBuild.hxml = build
		buildPath = os.path.dirname(build);

		# print("build file exists")
		f = codecs.open( build , "r+" , "utf-8" , "ignore" )
		while 1:
			l = f.readline() 
			if not l : 
				break;
			if l.startswith("--next") :
				builds.append( currentBuild )
				currentBuild = hxbuild.HaxeBuild()
				currentBuild.hxml = build
				
			l = l.strip()
			
			if l.startswith("-main") :
				spl = l.split(" ")
				if len( spl ) == 2 :
					currentBuild.main = spl[1]
				else :
					sublime.status_message( "Invalid build.hxml : no Main class" )
			
			if l.startswith("-lib") :
				spl = l.split(" ")
				if len( spl ) == 2 :
					lib = hxlib.HaxeLib.get( spl[1] )
					currentBuild.libs.append( lib )
				else :
					sublime.status_message( "Invalid build.hxml : lib not found" )

			if l.startswith("-cmd") :
				spl = l.split(" ")
				currentBuild.args.append( ( "-cmd" , " ".join(spl[1:]) ) )

			#if l.startswith("--connect") and HaxeComplete.instance().serverMode :
			#	currentBuild.args.append( ( "--connect" , str(self.serverPort) ))
			
			for flag in [ "lib" , "D" , "swf-version" , "swf-header", "debug" , "-no-traces" , "-flash-use-stage" , "-gen-hx-classes" , "-remap" , "-no-inline" , "-no-opt" , "-php-prefix" , "-js-namespace" , "-interp" , "-macro" , "-dead-code-elimination" , "-remap" , "-php-front" , "-php-lib", "-dce" , "-js-modern" ] :
				if l.startswith( "-"+flag ) :
					currentBuild.args.append( tuple(l.split(" ") ) )
					
					break
			
			for flag in [ "resource" , "xml" , "x" , "swf-lib" ] :
				if l.startswith( "-"+flag ) :
					spl = l.split(" ")
					outp = os.path.join( folder , " ".join(spl[1:]) )
					currentBuild.args.append( ("-"+flag, outp) )
					
					break

			for flag in hxbuild.HaxeBuild.targets :
				if l.startswith( "-" + flag + " " ) :
					spl = l.split(" ")
					#outp = os.path.join( folder , " ".join(spl[1:]) ) 
					outp = " ".join(spl[1:]) 
					currentBuild.args.append( ("-"+flag, outp) )
					
					currentBuild.target = flag
					currentBuild.output = outp
					break

			if l.startswith("-cp "):
				cp = l.split(" ")
				#view.set_status( "haxe-status" , "Building..." )
				cp.pop(0)
				classpath = " ".join( cp )
				main_folder = project.Project.main_folder()
				absClasspath = os.path.join( main_folder , classpath )
				currentBuild.classpaths.append( absClasspath )
				currentBuild.args.append( ("-cp" , absClasspath ) )
		
		if len(currentBuild.classpaths) == 0:
			print "no classpaths"
			currentBuild.classpaths.append( buildPath )
			currentBuild.args.append( ("-cp" , buildPath ) )
		
		if currentBuild.main is not None :
			builds.append( currentBuild )
	return builds

def find_nmml( folder ) :
	nmmls = glob.glob( os.path.join( folder , "*.nmml" ) )

	builds = []

	for build in nmmls:
		currentBuild = hxbuild.HaxeBuild()
		currentBuild.hxml = build
		currentBuild.nmml = build
		buildPath = os.path.dirname(build)

		# TODO delegate compiler options extractions to NME 3.2:
		# runcmd("nme diplay project.nmml nme_target")

		outp = "NME"
		f = codecs.open( build , "r+", "utf-8" , "ignore" )
		while 1:
			l = f.readline() 
			if not l : 
				break;
			m = extractTag.search(l)
			if not m is None:
				#print(m.groups())
				tag = m.group(1)
				name = m.group(3)
				if (tag == "app"):
					currentBuild.main = name
					mFile = re.search("\\b(file|title)=\"([a-z0-9_-]+)\"", l, re.I)
					if not mFile is None:
						outp = mFile.group(2)
				elif (tag == "haxelib"):
					currentBuild.libs.append( hxlib.HaxeLib.get( name ) )
					currentBuild.args.append( ("-lib" , name) )
				elif (tag == "classpath"):
					currentBuild.classpaths.append( os.path.join( buildPath , name ) )
					currentBuild.args.append( ("-cp" , os.path.join( buildPath , name ) ) )
			else: # NME 3.2
				mPath = re.search("\\bpath=\"([a-z0-9_-]+)\"", l, re.I)
				if not mPath is None:
					#print(mPath.groups())
					path = mPath.group(1)
					currentBuild.classpaths.append( os.path.join( buildPath , path ) )
					currentBuild.args.append( ("-cp" , os.path.join( buildPath , path ) ) )
		
		outp = os.path.join( folder , outp )
		currentBuild.target = "cpp"
		currentBuild.args.append( ("--remap", "flash:nme") )
		currentBuild.args.append( ("-cpp", outp) )
		currentBuild.output = outp

		if currentBuild.main is not None :
			builds.append( currentBuild )
	return builds



def select_nme_target( build, i, view ):
	target = hxbuild.HaxeBuild.nme_targets[i]
	if build.nmml is not None:
		hxbuild.HaxeBuild.nme_target = target
		view.set_status( "haxe-build" , build.to_string() )
		panel().status( "haxe-build" , build.to_string() )

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

def handle_completion_error(err, temp, fn, status):
	err = err.replace( temp , fn )
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

	errors = HaxeOutputConverter.extract_errors( err )

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
			toplevelComplete = skippable.search( skipped ) is None and inAnonymous.search( skipped ) is None

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

def get_haxe_actual_completion_data (completionCache, build, completeChar, view, macroCompletion, fn, offset, commas, src, run_haxe):
		inp = (fn,offset,commas,src[0:offset-1])
		

		
		lastInp = completionCache["inp"]

		useCache = lastInp is not None and inp == lastInp[0] and macroCompletion == lastInp[1]

		if useCache :
			ret, comps, status = completionCache["outp"]

		else :
			ret , haxeComps , status = run_haxe( view , build, fn + "@" + str(offset) , macroCompletion )
			

			if completeChar not in "(," : 
				comps = haxeComps
			else:
				comps = []

			completionCache["outp"] = (ret,comps,status)

		completionCache["inp"] = (inp, macroCompletion)

		return (ret, comps, status)

def make_cmd (serverMode, view, build, macroCompletion, settings, cwd, display):
		
	
	args = prepare_build_args_for_completion(serverMode, build, 
			macroCompletion, cwd, 
			hxsettings.HaxeSettings.showCompletionTimes(view), display)
	
		
	
	
		

	haxepath = hxsettings.HaxeSettings.haxeExec(view)

	cmd = [haxepath]
	for a in args :
		cmd.extend( list(a) )
	
	
	#print( cmd )
	#
	# TODO: replace runcmd with run_command('exec') when possible (haxelib, maybe build)
	#
	

	return cmd


class HaxeBuildHelper ():


	def __init__ (self):

		self.currentBuild = None
		self.selectingBuild = False
		self.builds = []


	def generate_build(self, view) :

		fn = view.file_name()

		if self.currentBuild is not None and fn == self.currentBuild.hxml and view.size() == 0 :	
			e = view.begin_edit()
			hxmlSrc = self.currentBuild.make_hxml()
			view.insert(e,0,hxmlSrc)
			view.end_edit(e)


	def select_build( self , view ) :
		scopes = view.scope_name(view.sel()[0].end()).split()
		
		if 'source.hxml' in scopes:
			view.run_command("save")

		self.extract_build_args( view , True )


	# called everytime a view is activated
	# changes the build
	def extract_build_args( self , view , forcePanel = False ) :
		
		self.builds = []

		fn = view.file_name()


		settings = view.settings()

		print "filename: " + fn

		folder = os.path.dirname(fn)
		

		folders = view.window().folders()
		print folders
		for f in folders:
			self.builds.extend(find_hxml(f))
			self.builds.extend(find_nmml(f))
				

		
		print "num builds:" + str(len(self.builds))

		# settings.set("haxe-complete-folder", folder)
		

		if len(self.builds) == 1:
			if forcePanel : 
				sublime.status_message("There is only one build")

			# will open the build file
			#if forcePanel :
			#	b = self.builds[0]
			#	f = b.hxml
			#	v = view.window().open_file(f,sublime.TRANSIENT) 

			self.set_current_build( view , int(0), forcePanel )

		elif len(self.builds) == 0 and forcePanel :
			sublime.status_message("No hxml or nmml file found")

			f = os.path.join(folder,"build.hxml")

			self.currentBuild = None
			self.get_build(view)
			self.currentBuild.hxml = f

			#for whatever reason generate_build doesn't work without transient
			v = view.window().open_file(f,sublime.TRANSIENT)

			self.set_current_build( view , int(0), forcePanel )

		elif len(self.builds) > 1 and forcePanel :
			buildsView = []
			for b in self.builds :
				#for a in b.args :
				#	v.append( " ".join(a) )
				buildsView.append( [b.to_string(), os.path.basename( b.hxml ) ] )

			self.selectingBuild = True
			sublime.status_message("Please select your build")
			view.window().show_quick_panel( buildsView , lambda i : self.set_current_build(view, int(i), forcePanel) , sublime.MONOSPACE_FONT )

		elif settings.has("haxe-build-id"):
			self.set_current_build( view , int(settings.get("haxe-build-id")), forcePanel )
		
		else:
			self.set_current_build( view , int(0), forcePanel )


	def set_current_build( self , view , id , forcePanel ) :
		
		print "set_current_build"
		if id < 0 or id >= len(self.builds) :
			id = 0
		
		view.settings().set( "haxe-build-id" , id )	

		if len(self.builds) > 0 :
			self.currentBuild = self.builds[id]
			print "set_current_build - 2"
			panel().status( "haxe-build" , self.currentBuild.to_string() )
		else:
			panel().status( "haxe-build" , "No build" )
			
		self.selectingBuild = False
 
		if forcePanel and self.currentBuild is not None: # choose NME target
			if self.currentBuild.nmml is not None:
				sublime.status_message("Please select a NME target")
				nme_targets = []
				for t in hxbuild.HaxeBuild.nme_targets :
					nme_targets.append( t[0] )

				view.window().show_quick_panel(nme_targets, lambda i : select_nme_target(self.currentBuild, i, view))

	def clear_build( self  ) :
		self.currentBuild = None

	def get_build( self , view ) :
		
		if self.currentBuild is None and view.score_selector(0,"source.haxe.2") > 0 :

			fn = view.file_name()

			src_dir = os.path.dirname( fn )

			src = view.substr(sublime.Region(0, view.size()))
		
			build = hxbuild.HaxeBuild()
			build.target = "js"

			folder = os.path.dirname(fn)
			folders = view.window().folders()
			for f in folders:
				if f in fn :
					folder = f

			pack = []
			for ps in packageLine.findall( src ) :
				if ps == "":
					continue
					
				pack = ps.split(".")
				for p in reversed(pack) : 
					spl = os.path.split( src_dir )
					if( spl[1] == p ) :
						src_dir = spl[0]

			cl = os.path.basename(fn)
			cl = cl.encode('ascii','ignore')
			cl = cl[0:cl.rfind(".")]

			main = pack[0:]
			main.append( cl )
			build.main = ".".join( main )

			build.output = os.path.join(folder,build.main.lower() + ".js")

			print "add cp: " + src_dir

			build.args.append( ("-cp" , src_dir) )
			#build.args.append( ("-main" , build.main ) )

			build.args.append( ("-js" , build.output ) )
			#build.args.append( ("--no-output" , "-v" ) )

			build.hxml = os.path.join( src_dir , "build.hxml")
			
			#build.hxml = os.path.join( src_dir , "build.hxml")
			self.currentBuild = build
			
		return self.currentBuild	


class PanelHelper ():

	def __init__ (self):
		self.panel = None


	def clear_output_panel(self, view) :
		win = view.window()

		self.panel = win.get_output_panel("haxe")

	def panel_output( self , view , text , scope = None ) :
		win = view.window()
		if self.panel is None :
			self.panel = win.get_output_panel("haxe")

		panel = self.panel

		text = datetime.now().strftime("%H:%M:%S") + " " + text;
		
		edit = panel.begin_edit()
		region = sublime.Region(panel.size(),panel.size() + len(text))
		panel.insert(edit, panel.size(), text + "\n")
		panel.end_edit( edit )

		if scope is not None :
			icon = "dot"
			key = "haxe-" + scope
			regions = panel.get_regions( key );
			regions.append(region)
			panel.add_regions( key , regions , scope , icon )
		#print( err )
		win.run_command("show_panel",{"panel":"output.haxe"})

		return self.panel


def hx_query_completion(view, offset, build, cache, run_haxe):
	id = view.id() 
	now = time.time()
	macroComp = False
	if id in haxe.commands.HaxeDisplayMacroCompletion.completions:
		oldTime = haxe.commands.HaxeDisplayMacroCompletion.completions[id]
		del haxe.commands.HaxeDisplayMacroCompletion.completions[id]

		if (now - oldTime) < 500:
			print "do macro completion"
			macroComp = True

	

	comps = get_haxe_completions( build, cache, run_haxe, view , offset, macroComp )
	return comps

def hxsl_query_completion(view, offset):
	return get_hxsl_completions( view , offset )
def hxml_query_completion(view, offset):
	return get_hxml_completions( view , offset )

class HaxeComplete( sublime_plugin.EventListener ):

	#folder = ""
	#buildArgs = []
	
	errors = []
 
	currentCompletion = {
		"inp" : None,
		"outp" : None
	}

	stdPaths = []
	stdPackages = []
	stdClasses = ["Void","String", "Float", "Int", "UInt", "Bool", "Dynamic", "Iterator", "Iterable", "ArrayAccess"]
	#stdClasses = []
	stdCompletes = []

	panel = None
	initialized = False
	inst = None
	
	@staticmethod
	def instance (): 
		if not HaxeComplete.initialized:

			classes, packs, ver, stdPaths = collect_compiler_info()

			HaxeComplete.stdPaths = stdPaths
			HaxeComplete.stdClasses.extend( classes )
			HaxeComplete.stdPackages.extend( packs )

			

			if ver is not None :
				HaxeComplete.inst.server.serverMode = int(ver.group(1)) >= 209

			#print "init HaxeComplete finished"

			HaxeComplete.initialized = True

		print "currentCompl: " + str(HaxeComplete.inst.currentCompletion)
		return HaxeComplete.inst

	def __init__(self):
		
		self.server = haxe.completion_server.CompletionServer(6000, True)
		self.panel_helper = PanelHelper()
		self.build_helper = HaxeBuildHelper()
		HaxeComplete.inst = self
		
		
		#self.start_server()
		
	def __del__(self) :
		self.server.stop_server()	
		

	def on_load( self, view ) :

		
		if view == None: 
			return

		fn = view.file_name()
		
		if (fn == None): 
			print "on_load haxe_complete file_name is None"
			return		
		else:
			print "onload haxe_complete file_name is " + str(view.file_name())

		if ViewTools.is_unsupported(view):
			return

		if ViewTools.is_haxe(view):
			HaxeCreateType().on_activated( view )
		
		
		self.build_helper.generate_build( view )
		highlight_errors( self.errors, view )


	def on_post_save( self , view ) :
		if ViewTools.is_hxml(view):
			self.build_helper.clear_build()
			self.clear_completion()

	# view is None when it's a preview

	def on_activated( self , view ) :
		
		if (view == None): 
			return

		fn = view.file_name()
		
		if (fn == None): 
			print "on_activated haxe_complete file_name is None"
			return		
		else:
			print "on_activated haxe_complete file_name is " + str(view.file_name())

		if (ViewTools.is_unsupported(view)):
			return
		
		if ViewTools.is_haxe(view) :
			HaxeCreateType().on_activated( view )
		
		self.build_helper.get_build(view)
		self.build_helper.extract_build_args( view )
		
		self.build_helper.generate_build(view)
		highlight_errors( self.errors, view )

	def on_pre_save( self , view ) :

		if not ViewTools.is_haxe(view) :
			return []

		
		ViewTools.create_missing_folders(view)
		

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



	def run_build( self , view ) :
		print "run build"
		err, comps, status = self.run_haxe( view )
		view.set_status( "haxe-status" , status )
		panel().status( "haxe-status" , status )
		print status
		
	
	def clear_completion (self):
		self.currentCompletion = {
				"inp" : None,
				"outp" : None
		}

	


	def run_haxe_simple( self, build, view , display, macroCompletion = False ) :

		self.server.start_server( view )
			
				
		fn = view.file_name()
		#src = view.substr(sublime.Region(0, view.size()))
		#src_dir = os.path.dirname(fn)
		tdir = os.path.dirname(fn)
		temp = os.path.join( tdir , os.path.basename( fn ) + ".tmp" )

		comps = [] 

		self.errors = [] 

		settings = view.settings()
 
		cwd = os.path.dirname( build.hxml ) 
		 
		#buildArgs = view.window().settings
		
		

		# TODO if we are in a macro block, remove the current target and set neko as target
		serverMode = haxe.settings.HaxeSettings.getBool('haxe-use-server-mode', True) and self.server.serverMode
 		cmd = make_cmd(serverMode, view, build, macroCompletion, settings, cwd, display)
			


		res, err = runcmd( cmd, "" )
		return (view, fn, temp, comps, view, cmd, build, res, err)

	def run_haxe( self, build, view , display , macroCompletion = False ) :

		(view, fn, temp, comps, view, cmd, 
			build, res, err) = self.run_haxe_simple(view, build, display, macroCompletion)

		
		return self.handle_normal_completion_output(fn, temp, comps, view, cmd, True, build, res, err)		
	

	def handle_normal_completion_output(self, fn, temp, comps, view, cmd, autocomplete, build, res, err):
		print(err)
		
		if not autocomplete :
			print "use panel"
			self.panel_helper.panel_output( view , " ".join(cmd) )

		#print( res.encode("utf-8") )
		status = ""

		if (not autocomplete) and (build.hxml is None) :
			#status = "Please create an hxml file"
			self.build_helper.extract_build_args( view , True )
		elif not autocomplete :
			# default message = build success
			status = "Build success"

		
		#print(err)	
		hints = []
		tree = None
		
		try :
			x = "<root>"+err.encode('utf-8')+"</root>";
			tree = ElementTree.XML(x);
			
		except Exception, e:
		#	print(e)
			print("invalid xml")
		


		if tree is not None :

			type_hints = HaxeOutputConverter.get_type_hint(tree.getiterator("type"))
			hints.extend(type_hints)
			

			if len(hints) > 0 :
				status = " | ".join(hints)
				
			li = tree.find("list")
			
			fields = HaxeOutputConverter.collect_completion_fields(li)
			comps.extend(fields)

		if len(hints) == 0 and len(comps) == 0:
			status, errors = handle_completion_error(err, temp, fn, status)
			self.errors = errors
			highlight_errors( errors, view )

			

		#print(status)
		return ( err, comps, status )

	def on_query_completions(self, view, prefix, locations):
		print "on_query_completion"


		pos = locations[0]
		
		offset = pos - len(prefix)
		comps = []

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
				# get build and maybe use cache
				build = self.build_helper.get_build( view ).copy()
				cache = self.currentCompletion
				comps = hx_query_completion(view, offset, build, cache, self.run_haxe)
				#print str(comps)
			
		return comps
	



#sublime.set_timeout(HaxeLib.scan, 200)