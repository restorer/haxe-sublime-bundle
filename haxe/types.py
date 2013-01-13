import time,os, codecs, glob

import haxe.haxe_complete as hc
import haxe.hxtools as hxtools



cache_time_ms = 30000 # in milliseconds
type_cache = {}

def log (msg):
	print msg



def find_types (classpaths, libs, base_path):
	classes = []
	packs = []

	cp = []
	cp.extend( classpaths )

	for lib in libs :
		if lib is not None :
			cp.append( lib.path )


	for path in cp :
		c, p = extract_types( os.path.join( base_path, path ) )
		classes.extend( c )
		packs.extend( p )

	
	
	classes.sort()
	packs.sort()

	return classes,packs


def extract_types( path , depth = 0 ) :

	now = time.time()

	if path in type_cache:
		old_time = type_cache[path][1]
		
		if (now - old_time) < cache_time_ms:
			log("use-type-cache")
			return type_cache[path][0]
		else:
			del type_cache[path]

	classes = []
	packs = []
	hasClasses = False
	
	for fullpath in glob.glob( os.path.join(path,"*.hx") ) : 
		f = os.path.basename(fullpath)

		cl, ext = os.path.splitext( f )
							
		if cl not in hc.HaxeComplete.stdClasses:
			s = codecs.open( os.path.join( path , f ) , "r" , "utf-8" , "ignore" )
			src = hxtools.comments.sub( "" , s.read() )
			
			clPack = "";
			for ps in hxtools.packageLine.findall( src ) :
				clPack = ps
			
			if clPack == "" :
				packDepth = 0
			else:
				packDepth = len(clPack.split("."))

			for decl in hxtools.typeDecl.findall( src ):
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
											
			if os.path.isdir( os.path.join( path , f ) ) and f not in hc.HaxeComplete.stdPackages :
				packs.append( f )
				subclasses,subpacks = extract_types( os.path.join( path , f ) , depth + 1 )
				for cl in subclasses :
					classes.append( f + "." + cl )
				
	classes.sort()
	packs.sort()

	type_cache[path] = ((list(classes), list(packs)), now)

	return classes, packs