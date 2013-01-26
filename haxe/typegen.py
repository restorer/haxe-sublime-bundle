import sublime, sublime_plugin
import os

import haxe.project as hxproject
import haxe.hxtools as hxtools

from haxe.log import log

class HaxeCreateType( sublime_plugin.WindowCommand ):

	classpath = None
	currentFile = None
	currentSrc = None

	def run( self , paths = [] , t = "class" ) :
		log("createtype")
		
		view = sublime.active_window().active_view()

		project = hxproject.current_project(view)

		builds = project.builds

		scopes = view.scope_name(view.sel()[0].end()).split()
		
		pack = [];

		if len(builds) == 0 :
			project.extract_build_args(view)

		if len(paths) == 0 :
			fn = view.file_name()
			paths.append(fn)

		log(paths)
		for path in paths :

			if os.path.isfile( path ) :
				path = os.path.dirname( path )

			if HaxeCreateType.classpath is None :
				HaxeCreateType.classpath = path

			for b in builds :
				for cp in b.classpaths :
					if path.startswith( cp ) :
						HaxeCreateType.classpath = path[0:len(cp)]
						for p in path[len(cp):].split(os.sep) :
							if "." in p : 
								break
							elif p :
								pack.append(p)

		if HaxeCreateType.classpath is None :
			if len(builds) > 0 :
				HaxeCreateType.classpath = builds[0].classpaths[0]

		# so default text ends with .
		if len(pack) > 0 :
			pack.append("")
						
		win = sublime.active_window()
		sublime.status_message( "Current classpath : " + HaxeCreateType.classpath )
		win.show_input_panel("Enter "+t+" name : " , ".".join(pack) , lambda inp: self.on_done(inp, t) , self.on_change , self.on_cancel )

	def on_done( self , inp, cur_type ) :

		fn = self.classpath;
		parts = inp.split(".")
		pack = []

		while( len(parts) > 0 ):
			p = parts.pop(0)
			
			fn = os.path.join( fn , p )
			if hxtools.is_type.match( p ) : 
				cl = p
				break;
			else :
				pack.append(p)

		if len(parts) > 0 :
			cl = parts[0]

		fn += ".hx"
		
		HaxeCreateType.currentFile = fn
		
		src = "\npackage " + ".".join(pack) + ";\n\n"+cur_type+" "+cl+" " 
		if cur_type == "typedef" :
			src += "= "
		src += "{\n\n\t\n\n}"
		HaxeCreateType.currentSrc = src

		sublime.active_window().open_file( fn )
 

	def on_change( self , inp ) :
		#sublime.status_message( "Current classpath : " + HaxeCreateType.classpath )
		log( inp )

	def on_cancel( self ) :
		None

class HaxeCreateTypeListener( sublime_plugin.EventListener ):

	def on_activated( self, view ) : 
		self.create_file(view)		

	def on_load (self, view):
		self.create_file(view)

	def create_file(self, view):
		if view is not None and view.file_name() != None and view.file_name() == HaxeCreateType.currentFile and view.size() == 0 :
			e = view.begin_edit()
			view.insert(e,0,HaxeCreateType.currentSrc)
			view.end_edit(e)
			sel = view.sel()
			sel.clear()
			pt = view.text_point(5,1)
			sel.add( sublime.Region(pt,pt) )