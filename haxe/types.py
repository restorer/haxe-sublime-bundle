import os, codecs, glob, re

from haxe import config as hxconfig
from haxe.tools import hxsrctools
from haxe.log import log


def find_types (classpaths, libs, base_path, filtered_classes = None, filtered_packages = None, include_private_types = True):

	bundle = hxsrctools.empty_type_bundle()

	cp = []
	cp.extend( classpaths )

	for lib in libs :
		if lib is not None :
			cp.append( lib.path )

	for path in cp :

		p = os.path.join( base_path, path )

		b = extract_types( p, filtered_classes, filtered_packages, 0, [], include_private_types )

		bundle = bundle.merge(b)

	return bundle

valid_package = re.compile("^[_a-z][a-zA-Z0-9_]*$")

def is_valid_package (pack):
	return valid_package.match(pack) and pack != "_std"

def extract_types( path , filtered_classes = None, filtered_packages = None, depth = 0, pack = [], include_private_types = True) :
	if filtered_classes is None: 
		filtered_classes = []
	if filtered_packages is None: 
		filtered_packages = []
	
	bundle = hxsrctools.empty_type_bundle()
	
	for fullpath in glob.glob( os.path.join(path,"*.hx") ) : 
		f = os.path.basename(fullpath)

		cl, ext = os.path.splitext( f )
							
		if cl not in filtered_classes:
			module_bundle = extract_types_from_file(os.path.join( path , f ), cl, include_private_types)
			bundle = bundle.merge(module_bundle)
	
	for f in os.listdir( path ) :
		if is_valid_package(f):
			cl, ext = os.path.splitext( f )
			
			cur_pack_base = ".".join(pack) + "." if len(pack) > 0 else ""

			cur_pack = cur_pack_base + f

			if os.path.isdir( os.path.join( path , f ) ) and cur_pack not in filtered_packages and cur_pack not in hxconfig.ignored_packages:
				next_pack = list(pack)
				next_pack.append(f)
				
				sub_bundle = extract_types( os.path.join( path , f ) , filtered_classes, filtered_packages, depth + 1, next_pack, include_private_types )
				bundle = bundle.merge(sub_bundle)
				
	return bundle

file_type_cache = {}



def extract_types_from_file (file, module_name = None, include_private_types = True):

	mtime = os.path.getmtime(file)
	if file in file_type_cache and file_type_cache[file][0] == mtime:
		return file_type_cache[file][1]

	# use cache based on last file modification

	if module_name == None:
		module_name = os.path.splitext( os.path.basename(file) )[0]

	s = codecs.open( file , "r" , "utf-8" , "ignore" )
	src = hxsrctools.strip_comments(s.read())
	

	bundle = hxsrctools.get_types_from_src(src, module_name, file)

	file_type_cache[file] = (mtime, bundle)

	return bundle

