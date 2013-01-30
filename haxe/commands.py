import sublime, sublime_plugin
import os
import re
import json
from sublime import Region

import haxe.project as hxproject
import haxe.codegen
import haxe.tools.path as path_tools
import haxe.hxtools as hxsrctools
import haxe.settings as hxsettings
from haxe.log import log

import haxe.tools.view as view_tools
import haxe.temp as hxtemp



#class HaxelibExecCommand(stexec.ExecCommand):
#
#	def run(self, *args, **kwargs):
#
#		print "hello running"
#		super(HaxelibExecCommand, self).run(*args, **kwargs)
#
#	def finish(self, *args, **kwargs):
#		super(HaxelibExecCommand, self).finish(*args, **kwargs)  
#		print "haxelibExec"
#		hxlib.HaxeLib.scan()

word_chars = re.compile("[a-z0-9_]", re.I)

class HaxeFindDeclarationCommand( sublime_plugin.TextCommand ):
	def run( self , edit ) :
		self.run1(True, False)

	def run1 (self, use_display, inline_workaround = False):
		print "HaxeFindDeclarationCommand"
		view = self.view

		file_name = view.file_name()

		if file_name == None:
			return

		project = hxproject.current_project(view)
		build = project.get_build(view).copy()
		build.args.append(("-D", "no-inline"))

		src = view_tools.get_content(view)

		file_name = os.path.basename(view.file_name())

		

		using_line = "\nusing hxsublime.FindDeclaration;\n"

		pos = view.sel()[0].a

		word = view.word(pos)

		word_start = word.a
		word_end = word.b

		log(src[word_end:len(src)])
		
		word_str = src[word_start:word_end]
		log(word_str)

		

		

		prev = src[word_start-1]

		
		field_access = False
		if prev == ".":
			field_access = True

		log(field_access)


		log(pos)
		log(word)
		add = ".sublime_find_decl()"

		if use_display:
			add += ".|"

		start = src[0:word_start]

		end = src[word_end:]

		if inline_workaround:
			add_x = "sublime_find_decl"			
			add_y = ""
			if use_display:
				add_y = ".|"
			new_src = start + add_x + "(" + word_str + ")" + add_y + end;
		else:
			new_src = start + word_str + add + end;

		package_decl = re.search(hxsrctools.package_line, new_src)

		if (package_decl == None):
			new_src = using_line + new_src
			log("new_src: " + new_src)
		else:
			new_src = new_src[0:package_decl.end(0)]+using_line+new_src[package_decl.end(0):len(new_src)]
			log("new_src: " + new_src)

		temp_path, temp_file = hxtemp.create_temp_path_and_file(build, view.file_name(), new_src)

		log("here we go")
		build.add_classpath(temp_path)
		
		if use_display:
			build.set_auto_completion(temp_file + "@0", False, False)

		server_mode = project.is_server_mode()

		log("run")
		out, err = build.run(hxsettings.haxe_exec(), server_mode, view, project)
		log("run complete")
		hxtemp.remove_path(temp_path)
		

		file_pos = re.compile("\|\|\|\|\|([^|]+)\|\|\|\|\|", re.I)

		res = re.search(file_pos, out)
		if res != None:

			log("found position")

			

			json_str = res.group(1)

			json_res = json.loads(json_str)

			log(json_res)

			if "file" in json_res:
				file = json_res["file"]
				min = json_res["min"]
				max = json_res["max"]

				




				log(file)
				log(min)
				log(max)



				#abs_path = abs_path.replace(build.get_relative_path(temp_file), build.get_relative_path(view.file_name())
				
				log("temp_path: " + temp_path)
				log("temp_file: " + temp_file)
				abs_path = path_tools.join_norm(build.get_build_folder(), file)
				abs_path_temp = path_tools.join_norm(build.get_build_folder(), build.get_relative_path(os.path.join(temp_path, temp_file)))

				log("build_rel: " + build.get_relative_path(os.path.join(temp_path, temp_file)))
				log("abs_path: " + abs_path)
				log("abs_path_temp: " + abs_path_temp)

				

				if (abs_path == temp_file):
					
					abs_path = view.file_name()
					target_view = view
					m = min
					log("word_end: " + str(word_end))
					log("min: " + str(min))
					if min > word_end:
						m -= len(add)
					m -= len(using_line)
					target_view.sel().clear()
					target_view.sel().add(sublime.Region(m))
					target_view.show(sublime.Region(m))
					#target_view.sel().clear()
					#target_view.sel().add(sublime.Region(min))
				else:
					target_view = view.window().open_file(abs_path)
					
					def f():
						if target_view.is_loading() == False:
							
							
							
							target_view.sel().clear()
							target_view.sel().add(sublime.Region(min))
							target_view.show(sublime.Region(min))
							
						else:
							sublime.set_timeout(f, 100)

					sublime.set_timeout(f, 100)

				


			elif "error" in json_res:
				error = json_res["error"]
				log(error)
				if (error =="inlined" and not inline_workaround):
					self.run1(use_display, True)
			else:
				log("nothing found try again")
				if use_display:

					self.run1(False)
		else:
			log("nothing found, try again")
			if use_display:
				self.run1(False)

			
			

			#log(new_src.find_all(hxsrctools.type_decl))

			# remove temp path and file
			#




class HaxeGetTypeOfExprCommand (sublime_plugin.TextCommand ):
	def run( self , edit ) :
		

		view = self.view
		
		file_name = view.file_name()

		if file_name == None:
			return

		file_name = os.path.basename(view.file_name())

		window = view.window()
		folders = window.folders()
 
		project_dir = folders[0]
		tmp_folder = folders[0] + "/tmp"
		target_file = folders[0] + "/tmp/" + file_name

		if os.path.exists(tmp_folder):
			path_tools.remove_dir(tmp_folder)			
		

		os.makedirs(tmp_folder)
		

		fd = open(target_file, "w+")
		sel = view.sel()

		word = view.substr(sel[0])

		replacement = "(hxsublime.Utils.getTypeOfExpr(" + word + "))."

		newSel = Region(sel[0].a, sel[0].a + len(replacement))


		view.replace(edit, sel[0], replacement)

		newSel = view.sel()[0]

		view.replace(edit, newSel, word)

		new_content = view.substr(sublime.Region(0, view.size()))
		fd.write(new_content)

		view.run_command("undo")


class HaxeDisplayCompletion( sublime_plugin.TextCommand ):

	def run( self , edit ) :

		log("run HaxeDisplayCompletion")
		
		view = self.view
		project = hxproject.current_project(view)
		project.completion_context.set_manual_trigger(view, False)
		

		self.view.run_command( "auto_complete" , {
			"api_completions_only" : True,
			"disable_auto_insert" : True,
			"next_completion_if_showing" : False,
			'auto_complete_commit_on_tab': True
		})


class HaxeDisplayMacroCompletion( sublime_plugin.TextCommand ):
	
	def run( self , edit ) :
		
		log("run HaxeDisplayMacroCompletion")
		
		view = self.view
		project = hxproject.current_project(view)
		project.completion_context.set_manual_trigger(view, True)
		
		
		view.run_command( "auto_complete" , {
			"api_completions_only" : True,
			"disable_auto_insert" : True,
			"next_completion_if_showing" : False,
			'auto_complete_commit_on_tab': True
		} )

		

class HaxeInsertCompletionCommand( sublime_plugin.TextCommand ):
	
	def run( self , edit ) :
		log("run HaxeInsertCompletion")
		view = self.view

		view.run_command( "insert_best_completion" , {
			"default" : ".",
			"exact" : True
		} )

class HaxeSaveAllAndBuildCommand( sublime_plugin.TextCommand ):
	def run( self , edit ) :
		log("run HaxeSaveAllAndBuildCommand")
		view = self.view
		view.window().run_command("save_all")
		hxproject.current_project(self.view).run_build( view )

class HaxeRunBuildCommand( sublime_plugin.TextCommand ):
	def run( self , edit ) :
		view = self.view
		log("run HaxeRunBuildCommand")
		project = hxproject.current_project(self.view)

		if len(project.builds) == 0:
			log("no builds available")
			project.extract_build_args(view, True);
		else:
			project.run_build( view )


class HaxeSelectBuildCommand( sublime_plugin.TextCommand ):
	def run( self , edit ) :
		log("run HaxeSelectBuildCommand")
		view = self.view
		
		hxproject.current_project(self.view).select_build( view )

# called 
class HaxeHintCommand( sublime_plugin.TextCommand ):
	def run( self , edit ) :
		log("run HaxeHintCommand")
		
		view = self.view
		
		view.run_command('auto_complete', {'disable_auto_insert': True})
		


class HaxeRestartServerCommand( sublime_plugin.WindowCommand ):

	def run( self ) : 
		log("run HaxeRestartServerCommand")
		view = sublime.active_window().active_view()
		
		project = hxproject.current_project(self.view)

		project.server.stop_server()
		project.server.start_server( view )



class HaxeGenerateUsingCommand( sublime_plugin.TextCommand ):
	def run( self , edit ) :
		log("run HaxeGenerateUsingCommand")
		haxe.codegen.generate_using(self.view, edit)
		

class HaxeGenerateImportCommand( sublime_plugin.TextCommand ):

	def run( self, edit ) :
		log("run HaxeGenerateImportCommand")
		
		haxe.codegen.generate_import(self.view, edit)
		


# stores the info for file creation, is shared between the command and listener instances.
current_create_type_info = {}

class HaxeCreateTypeCommand( sublime_plugin.WindowCommand ):

	
	

	def __init__ (self, win):
		
		self.classpath = None
		self.win = win


	def run( self , paths = [] , t = "class" ) :
		log("createtype")
		
		win = self.win		
		view = win.active_view()

		project = hxproject.current_project(view)

		builds = project.builds

		#scopes = view.scope_name(view.sel()[0].end()).split()
		
		pack = [];

		if len(builds) == 0 and view != None and view.file_name() != None:
			print view.file_name()
			project.extract_build_args(view)

		if len(paths) == 0 and view != None:
			fn = view.file_name()
			paths.append(fn)

		log(paths)
		for path in paths :

			if os.path.isfile( path ) :
				path = os.path.dirname( path )

			if self.classpath is None :
				self.classpath = path

			for b in builds :
				for cp in b.classpaths :
					if path.startswith( cp ) :
						self.classpath = path[0:len(cp)]
						for p in path[len(cp):].split(os.sep) :
							if "." in p : 
								break
							elif p :
								pack.append(p)

		if self.classpath is None :
			if len(builds) > 0 :
				self.classpath = builds[0].classpaths[0]

		# so default text ends with .
		if len(pack) > 0 :
			pack.append("")
						
		
		sublime.status_message( "Current classpath : " + self.classpath )
		win.show_input_panel("Enter "+t+" name : " , ".".join(pack) , lambda inp: self.on_done(inp, t) , self.on_change , self.on_cancel )

	def on_done( self , inp, cur_type ) :

		fn = self.classpath;
		parts = inp.split(".")
		pack = []

		while( len(parts) > 0 ):
			p = parts.pop(0)
			
			fn = os.path.join( fn , p )
			if hxsrctools.is_type.match( p ) : 
				cl = p
				break;
			else :
				pack.append(p)

		if len(parts) > 0 :
			cl = parts[0]

		fn += ".hx"
		
		
		
		src = "\npackage " + ".".join(pack) + ";\n\n"+cur_type+" "+cl+" " 
		if cur_type == "typedef" :
			src += "= "
		src += "{\n\n\t\n\n}"

		current_create_type_info[fn] = src

		sublime.active_window().open_file( fn )
 

	def on_change( self , inp ) :
		#sublime.status_message( "Current classpath : " + self.classpath )
		log( inp )

	def on_cancel( self ) :
		None


class HaxeCreateTypeListener( sublime_plugin.EventListener ):


	def on_activated( self, view ) : 
		self.create_file(view)		

	def on_load (self, view):
		self.create_file(view)

	def create_file(self, view):
		if view is not None and view.file_name() != None and view.file_name() in current_create_type_info and view.size() == 0 :
			e = view.begin_edit()
			view.insert(e,0,current_create_type_info[view.file_name()])
			view.end_edit(e)
			sel = view.sel()
			sel.clear()
			pt = view.text_point(5,1)
			sel.add( sublime.Region(pt,pt) )



