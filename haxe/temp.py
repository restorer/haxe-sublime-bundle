import os
from haxe.tools import PathTools
import codecs

class TempClasspath:

	id = 0

	@staticmethod
	def get_temp_path(build):



		id = TempClasspath.id
		path = build.get_build_folder()

		if path is None:
			print "path of build is None"
			return None


		temp_path = os.path.join(path, ".hxsublime_tmp/tmp" + str(id))

		while os.path.exists(temp_path):
			id += 1
			temp_path = os.path.join(path, ".hxsublime_tmp/tmp" + str(id))
		
		
		return temp_path

	@staticmethod
	def create_temp_path(build):

		temp_path = TempClasspath.get_temp_path(build)
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


