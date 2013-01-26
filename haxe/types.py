import os, codecs, glob


from haxe.tools.cache import Cache
import haxe.hxtools as hxtools





def log (msg):
	print msg



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
type_cache = Cache(30000) 


def extract_types( path , filtered_classes = None, filtered_packages = None, depth = 0 ) :

	if filtered_classes is None: 
		filtered_classes = []
	if filtered_packages is None: 
		filtered_packages = []
	

	cached = type_cache.get_or_default(path)
	if cached != None:
		return cached
	

	classes = []
	packs = []
	has_classes = False
	
	for fullpath in glob.glob( os.path.join(path,"*.hx") ) : 
		f = os.path.basename(fullpath)

		cl, ext = os.path.splitext( f )
							
		if cl not in filtered_classes:
			module_classes = extract_types_from_file(os.path.join( path , f ), depth, cl)

			has_classes = has_classes or len(module_classes) > 0

			classes.extend(module_classes)
	
	# what happens if has_classes == 0 and depth = 1, could still be a valid classpath or not??
	if has_classes or depth == 0 : 
		
		for f in os.listdir( path ) :
			
			cl, ext = os.path.splitext( f )
											
			if os.path.isdir( os.path.join( path , f ) ) and f not in filtered_packages :
				packs.append( f )
				subclasses,subpacks = extract_types( os.path.join( path , f ) , filtered_classes, filtered_packages, depth + 1 )
				for cl in subclasses :
					classes.append( f + "." + cl )
				
	classes.sort()
	packs.sort()

	type_cache.insert(path, (list(classes), list(packs)))
	

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

	for decl in hxtools.type_decl.findall( src ):
		t = decl[1]

		if( pack_depth == depth ) :
			if t == module_name or module_name == "StdTypes":
				classes.append( t )
			else: 
				classes.append( module_name + "." + t )

	return classes