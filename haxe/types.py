import os, codecs, glob
import haxe.config as hxconfig
import haxe.hxtools as hxtools
from haxe.log import log
from haxe.tools.cache import Cache


def find_types (classpaths, libs, base_path, filtered_classes = None, filtered_packages = None):

	classes = []
	packs = []

	cp = []
	cp.extend( classpaths )

	for lib in libs :
		if lib is not None :
			cp.append( lib.path )


	for path in cp :

		c, p = extract_types( os.path.join( base_path, path ), filtered_classes, filtered_packages )

		classes.extend( c )
		packs.extend( p )

	
	
	classes.sort()
	packs.sort()

	return classes,packs


# 30 seconds cache
type_cache = Cache(1)


def extract_types( path , filtered_classes = None, filtered_packages = None, depth = 0, pack = [] ) :

	if filtered_classes is None: 
		filtered_classes = []
	if filtered_packages is None: 
		filtered_packages = []
	

	cached = type_cache.get_or_default(path)
	if cached != None:
		return cached
	

	classes = []
	packs = []
	
	for fullpath in glob.glob( os.path.join(path,"*.hx") ) : 
		f = os.path.basename(fullpath)

		cl, ext = os.path.splitext( f )
							
		if cl not in filtered_classes:
			module_classes = extract_types_from_file(os.path.join( path , f ), depth, cl)

			classes.extend(module_classes)
	
			
	for f in os.listdir( path ) :
		if f not in hxconfig.ignored_folders:
			cl, ext = os.path.splitext( f )
			
			cur_pack = ".".join(pack) + "." + f

			if os.path.isdir( os.path.join( path , f ) ) and cur_pack not in filtered_packages and cur_pack not in hxconfig.ignored_packages:
				next_pack = list(pack)
				next_pack.append(f)
				packs.append( cur_pack )
				subclasses,subpacks = extract_types( os.path.join( path , f ) , filtered_classes, filtered_packages, depth + 1, next_pack )
				for cl in subclasses :
					classes.append( f + "." + cl )
				
	classes.sort()
	packs.sort()

	type_cache.insert(path, (classes, packs))
	

	return classes, packs



def extract_types_from_file (file, depth, module_name = None):

	if module_name == None:
		module_name = os.path.splitext( os.path.basename(file) )[0]

	classes = []
	s = codecs.open( file , "r" , "utf-8" , "ignore" )
	src = hxtools.comments.sub( "" , s.read() )
	
	clPack = "";
	for ps in hxtools.package_line.findall( src ) :
		clPack = ps
	
	if clPack == "" :
		pack_depth = 0
	else:
		pack_depth = len(clPack.split("."))

	module_class_included = False

	for decl in hxtools.type_decl.findall( src ):
		t = decl[1]

		if( pack_depth == depth ) :
			if t == module_name or module_name == "StdTypes":
				classes.append( t )
				module_class_included = True
			else: 
				classes.append( module_name + "." + t )

	if (not module_class_included):
		classes.append( module_name )

	return classes