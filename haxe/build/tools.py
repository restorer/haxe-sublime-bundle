# -*- coding: utf-8 -*-
import os
import sys
import re
import glob
import codecs
import sublime

from haxe import config

from haxe.tools import pathtools

from haxe.execute import run_cmd
from haxe.log import log

from haxe.tools.stringtools import encode_utf8, to_unicode



from haxe.build.hxmlbuild import HxmlBuild
from haxe.build.nmebuild import NmeBuild
from haxe.build.openflbuild import OpenFlBuild

try:
	from io import StringIO
except:
	from StringIO import StringIO

# TODO refactor this method into smaller managable chunks
def _hxml_buffer_to_builds(project, hxml_buffer, folder, build_path, build_file = None, hxml = None):
	builds = []

	current_build = HxmlBuild(hxml, build_file)
	
	# print("build file exists")
	f = hxml_buffer
	while 1:
		l = f.readline() 
		if not l: 
			break;

		if l == "":
			continue

		l = l.strip()

		if l.startswith("#build-name="):
			current_build.name = l[12:]
			continue

		if l.startswith("#"):
			continue
		



		if l.startswith("--next") :
			if len(current_build.classpaths) == 0:
				log("no classpaths")
				current_build.add_classpath( build_path )
				#current_build.args.append( ("-cp" , build_path ) )
			#current_build.get_types()
			builds.append( current_build )
			current_build = HxmlBuild(hxml, build_file)
			continue
			
		
		
		if l.endswith(".hxml"):
			
			log("found ref of hxml file:" + l)
			path = os.path.dirname(hxml)
			sub_builds = _hxml_to_builds(project, path + os.sep + l, folder)
			if len(sub_builds) == 1:
				b = sub_builds[0]
				current_build.merge(b)

		if l.startswith("-main") :
			spl = l.split(" ")
			if len( spl ) == 2 :
				current_build.main = spl[1]
			else :
				sublime.status_message( "Invalid build.hxml : no Main class" )
		
		if l.startswith("-lib") :
			spl = l.split(" ")
			if len( spl ) == 2 :
				lib = project.haxelib_manager.get( spl[1] )
				if lib is not None:
					log("lib to build:" + str(lib))
					current_build.add_lib( lib )
				else:

					current_build.add_arg( ("-lib", spl[1] ) )
					from haxe import panel
					panel.default_panel().writeln("Error: haxelib library " + str(spl[1]) + " is not installed" )
			else :
				sublime.status_message( "Invalid build.hxml : lib not found" )

		if l.startswith("-cmd") :
			spl = l.split(" ")
			current_build.add_arg( ( "-cmd" , " ".join(spl[1:]) ) )
		
		if l.startswith("--macro"):
			spl = l.split(" ")
			current_build.add_arg( ( "--macro" , " ".join(spl[1:])  ) )	

		if l.startswith("-D"):
			tup = tuple(l.split(" "))
			current_build.add_arg( tup )
			current_build.add_define(tup[1])
			continue

		for flag in [ "swf-version" , "swf-header", 
					"debug" , "-no-traces" , "-flash-use-stage" , "-gen-hx-classes" , 
					"-remap" , "-no-inline" , "-no-opt" , "-php-prefix" , 
					"-js-namespace" , "-interp" , "-dead-code-elimination" , 
					"-php-front" , "-php-lib", "dce" , "-js-modern", "-times" ] :
			if l.startswith( "-"+flag ) :
				current_build.add_arg( tuple(l.split(" ") ) )
				
				break
		
		for flag in [ "resource" , "xml" , "x" , "swf-lib" , "java-lib" ] :
			if l.startswith( "-"+flag ) :
				spl = l.split(" ")
				outp = os.path.join( folder , " ".join(spl[1:]) )
				current_build.add_arg( ("-"+flag, outp) )
				if (flag == "x"):
					current_build.target = "neko"
				break

		for flag in config.targets:
			if l.startswith( "-" + flag + " " ) :
				spl = l.split(" ")

				outp = " ".join(spl[1:]) 
				current_build.add_arg( ("-"+flag, outp) )
				
				current_build.target = flag
				current_build.output = outp
				break

		if l.startswith("-cp "):
			cp = l.split(" ")
			
			cp.pop(0)
			classpath = " ".join( cp )
			
			abs_classpath = pathtools.join_norm( build_path , classpath )
			current_build.add_classpath( abs_classpath )
			#current_build.add_arg( ("-cp" , abs_classpath ) )
	
	if len(current_build.classpaths) == 0:
		log("no classpaths")
		current_build.add_classpath( build_path )
		#current_build.args.append( ("-cp" , build_path ) )

	#current_build.get_types()
	builds.append( current_build )

	return builds

def _find_build_files_in_folder(folder, extension):
	if not os.path.isdir(folder) :
		return []
		
	files = list(map(lambda x: (x, folder), glob.glob( os.path.join( folder , "*."+extension ) )))
	for dir in os.listdir(folder):
		f = os.path.join(folder, dir)
		files.extend(map(lambda x: (x, f), glob.glob( os.path.join( f , "*."+extension ) )) )
	return files

def _hxml_to_builds (project, hxml, folder):
	build_path = os.path.dirname(hxml);
	hxml_buffer = codecs.open( hxml , "r+" , "utf-8" , "ignore" )
	return _hxml_buffer_to_builds(project, hxml_buffer, folder, build_path, hxml, hxml)
	
_extract_tag = re.compile("<([a-z0-9_-]+).*?\s(name|main|title|file)=\"([ a-z0-9_./-]+)\"", re.I)

def _find_nme_project_title(nmml_file):
	f = codecs.open( nmml_file , "r+", "utf-8" , "ignore" )
	title = None
	while 1:
		l = f.readline()
		if not l :
			break
		m = _extract_tag.search(l)
		if not m is None:
			tag = m.group(1)
			
			if tag == "meta" or tag == "app" :
				mFile = re.search("\\b(file|title)=\"([ a-z0-9_-]+)\"", l, re.I)
				if not mFile is None:
					title = mFile.group(2)
					break
	f.close()
	return title

def create_haxe_build_from_nmml (project, target, nmml, display_cmd):

	cmd = list(display_cmd)
	cmd.append(nmml)
	cmd.append(target.plattform)
	cmd.extend(target.args)

	nmml_dir = os.path.dirname(nmml)

	out, err = run_cmd( cmd, cwd=nmml_dir )

	return _hxml_buffer_to_builds(project, StringIO(out), nmml_dir, nmml_dir, nmml, None)[0]

def find_hxml_projects( project, folder ) :
	
	builds = []
	found = _find_build_files_in_folder(folder, "hxml")
	for build in found:
		
		hxml_file = build[0]
		hxml_folder = build[1]
		
		b = _hxml_to_builds(project, hxml_file, hxml_folder)
		log("builds in hxml " + encode_utf8(hxml_file) + ":" + str(len(b)))
		builds.extend(b)

	return builds

def find_nme_projects( project, folder ) :
	found = _find_build_files_in_folder(folder, "nmml")
	builds = []
	for build in found:
		nmml_file = build[0]
		title = _find_nme_project_title(nmml_file)
		if title is not None:
			for t in config.nme_targets:
				builds.append(NmeBuild(project, title, nmml_file, t))
	return builds

def find_openfl_projects( project, folder ) :

	found = _find_build_files_in_folder(folder, "xml")
	builds = []
	for build in found:
		openfl_xml = build[0]
		title = _find_nme_project_title(openfl_xml)
		if title is not None:
			for t in config.openfl_targets:
				builds.append(OpenFlBuild(project, title, openfl_xml, t))


	return builds
