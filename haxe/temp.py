import os

import codecs
import tempfile

from haxe.log import log
from haxe.tools import pathtools

from haxe import exceptions

from haxe.tools.stringtools import encode_utf8, st2_to_unicode

def get_temp_path_id(build):

	
	path = build.get_build_folder()

	if path is None:
		raise exceptions.ExtractBuildPathException(build)

	path1 = "_".join("_".join(path.split(os.sep)).split(":"))

	temp_path = os.path.join(tempfile.gettempdir(), "haxe_sublime_hx" + path1 + "_")

	return temp_path

def create_temp_path(build):

	temp_path = get_temp_path_id(build)
	
	
	pathtools.remove_dir(temp_path)
	os.makedirs(temp_path)

	return temp_path

def create_file(temp_path, build, orig_file, content):
	orig_file = st2_to_unicode(orig_file)
	relative = build.get_relative_path(orig_file)
	log("relative:" + str(encode_utf8(relative)))
	if relative is None:
		raise exceptions.GetRelativePathException(build, orig_file)

	new_file = os.path.join(temp_path, relative)
	new_file_dir = os.path.dirname(new_file)
	if not os.path.exists(new_file_dir):
		os.makedirs(new_file_dir)
	
	f = codecs.open( new_file , "wb" , "utf-8" , "ignore" )
	f.write( content )
	f.close()
	return new_file

def create_temp_path_and_file(build, orig_file, content):
	temp_path = create_temp_path(build)
		
	temp_file = create_file(temp_path, build, orig_file, content)
	return temp_path, temp_file

def remove_path (temp_path):
	if temp_path is not None:
		pathtools.remove_dir(temp_path)
