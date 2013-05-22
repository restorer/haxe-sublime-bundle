import os
import haxe.tools.path as path_tools
import codecs


def get_temp_path(build):

	id = 0
	path = build.get_build_folder()

	if path is None:
		return None


	temp_path = os.path.join(path, os.path.join(".hxsublime_tmp","tmp" + str(id)))
	
	# while os.path.exists(temp_path):
	# 	id += 1
	# 	temp_path = os.path.join(path, os.path.join(".hxsublime_tmp","tmp" + str(id)))
	
	
	return temp_path

def create_temp_path(build):

	temp_path = get_temp_path(build)
	path_tools.remove_dir(temp_path)
	os.makedirs(temp_path)
	return temp_path

def create_file(temp_path, build, orig_file, content):
	relative = build.get_relative_path(orig_file)
	
	if relative is None:
		return None
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
	if temp_path is None:
		return None
	
	temp_file = create_file(temp_path, build, orig_file, content)
	return temp_path, temp_file


def remove_path (temp_path):
	pass
	#path_tools.remove_dir(temp_path)


 