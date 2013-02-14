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

	# use cache based on last file modification

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

	constructors = extract_enum_constructors_from_src(src, module_name, False)
	
	for c in constructors:

		if( pack_depth == depth ) :
			if c[0] == module_name or module_name == "StdTypes":
				classes.append( c[0] + "." + c[1] )
			else: 
				classes.append( module_name + "." + c[0] + "." + c[1] )	

	if (not module_class_included):
		classes.append( module_name )

	return classes


import re
enum_constructor_start_decl = re.compile("\s+([a-zA-Z0-9_]+)" , re.M )
enum_start_decl = re.compile("(private\s+)?enum\s+([A-Z][a-zA-Z0-9_]*)\s*(<[a-zA-Z0-9_,]+>)?" , re.M )

def extract_enum_constructors_from_src (src, module_name, include_private = False):

	all = []
	for e in enum_start_decl.finditer(src):
		if e.group(1) != None and not include_private:
			continue
		else:
			enum_name = e.group(2)
			start = search_next_char_on_same_level(src, "{", e.start(2))
			if start != None:
				end = search_next_char_on_same_level(src, "}", start[0]+1)
				if end != None:
					constructors = extract_enum_constructors_from_enum(src[start[0]+1: end[0]-1])
					all.extend([(enum_name,c) for c in constructors])
	return all




def extract_enum_constructors_from_enum (enumStr):
	
	constructors = []
	start = 0;
	while True:
		m = enum_constructor_start_decl.match(enumStr, start)
		if m != None:
			constructor = m.group(1)
			constructors.append(constructor)
			end = search_next_char_on_same_level(enumStr, ";", m.end(1))
			if end != None:
				start = end[0]+1
			else:
				break
		else:
			break
	return constructors

def search_next_char_on_same_level (str, char, start_pos):
	open_pars = 0
	open_braces = 0
	open_brackets = 0
	open_angle_brackets = 0

	count = len(str)
	cur = ""
	pos = start_pos
	while (True):
		if pos > count-1:
			break

		c = str[pos]

		next = str[pos+1] if pos < count-1 else None

		if (c == char and open_pars == 0 and open_braces == 0 and open_brackets == 0 and open_angle_brackets == 0):
			return (pos,cur)
						
		if (c == "-" and next == ">"):
			cur += "->"
			pos += 2
		elif (c == "{"):
			pos += 1
			open_braces += 1
			cur += c
		elif (c == "}"):
			pos += 1
			open_braces -= 1
			cur += c
		elif (c == "("):
			pos += 1
			open_pars += 1
			cur += c
		elif (c == ")"):
			pos += 1
			open_pars -= 1
			cur += c
		elif (c == "["):
			pos += 1
			open_brackets += 1
			cur += c
		elif (c == "]"):
			pos += 1
			open_brackets -= 1
			cur += c
		elif (c == "<"):
			pos += 1
			open_angle_brackets += 1
			cur += c
		elif (c == ">"):
			pos += 1
			open_angle_brackets -= 1
			cur += c
		else:
			pos += 1
			cur += c
	return None




print str(extract_enum_constructors_from_src("enum Xy_Z<A,B:{ x : Int, y : Void->String}> { Left(v:A); Right(v:B); }", "my.Module"))
print str(extract_enum_constructors_from_src("  enum Xy_Z<A,B:{ x : Int, y : Void->String}> { Left(v:A); Right(v:B); }", "my.Module"))
print str(extract_enum_constructors_from_src("enum XY{ Left; Right; }", "my.Module"))

