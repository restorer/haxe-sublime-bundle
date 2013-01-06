import haxe.haxe_complete




import sublime, sublime_plugin
import time





from sublime import Region

import haxe

import os

import re

import shutil




packageLine = re.compile("package\s*([a-z0-9.]*);", re.I)


def removeDir(path):
    if os.path.isdir(path):
        shutil.rmtree(path)

class HaxeGetTypeOfExprCommand (sublime_plugin.TextCommand ):
	def run( self , edit ) :
		

		view = self.view
		
		fileName = view.file_name()

		if fileName == None:
			return

		fileName = os.path.basename(view.file_name())

		window = view.window()
		folders = window.folders()
 
		projectDir = folders[0]
		tmpFolder = folders[0] + "/tmp"
		targetFile = folders[0] + "/tmp/" + fileName

		if os.path.exists(tmpFolder):
			removeDir(tmpFolder)			
		

		os.makedirs(tmpFolder)
		

		fd = open(targetFile, "w+")
		sel = view.sel()

		word = view.substr(sel[0])



		replacement = "(hxsublime.Utils.getTypeOfExpr(" + word + "))."

		newSel = Region(sel[0].a, sel[0].a + len(replacement))

		print(str(newSel))

		print "do replace"
		view.replace(edit, sel[0], replacement)

		newSel = view.sel()[0]

		view.replace(edit, newSel, word)

		newContent = view.substr(sublime.Region(0, view.size()))
		fd.write(newContent)


		
		

		view.run_command("undo")
		
		

		

		#print sel


class HaxeDisplayCompletion( sublime_plugin.TextCommand ):
	
	

	def run( self , edit ) :

		def f ():
			view = self.view
			s = view.settings();

			print("run_command: auto_complete")
			view.run_command( "auto_complete" , {
				"api_completions_only" : True,
				"disable_auto_insert" : True,
				"next_completion_if_showing" : True
			} )
		sublime.set_timeout(f, 0)




class HaxeDisplayMacroCompletion( sublime_plugin.TextCommand ):
	
	completions = {}

	def run( self , edit ) :
		print("completing")
		view = self.view
		s = view.settings();
		
		print str(s)

		HaxeDisplayMacroCompletion.completions[view.id()] = time.time()

		view.run_command( "auto_complete" , {
			"api_completions_only" : True,
			"disable_auto_insert" : True,
			"next_completion_if_showing" : True,
			"macroCompletion" : True
		} )

		

class HaxeInsertCompletion( sublime_plugin.TextCommand ):
	
	def run( self , edit ) :
		#print("insert completion")
		view = self.view

		view.run_command( "insert_best_completion" , {
			"default" : ".",
			"exact" : True
		} )

class HaxeSaveAllAndBuild( sublime_plugin.TextCommand ):
	def run( self , edit ) :
		complete = haxe.haxe_complete.HaxeComplete.instance()
		view = self.view
		view.window().run_command("save_all")
		complete.run_build( view )

class HaxeRunBuild( sublime_plugin.TextCommand ):
	def run( self , edit ) :
		complete = haxe.haxe_complete.HaxeComplete.instance()
		view = self.view
		
		complete.run_build( view )


class HaxeSelectBuild( sublime_plugin.TextCommand ):
	def run( self , edit ) :
		print "do select build"
		complete = haxe.haxe_complete.HaxeComplete.instance()
		view = self.view
		
		complete.select_build( view )


class HaxeHint( sublime_plugin.TextCommand ):
	def run( self , edit ) :
		#print("haxe hint")
		
		complete = haxe.haxe_complete.HaxeComplete.instance()
		view = self.view
		
		sel = view.sel()
		for r in sel :
			comps = complete.get_haxe_completions( self.view , r.end() )
			#print(status);
			#view.set_status("haxe-status", status)
			#sublime.status_message(status)
			#if( len(comps) > 0 ) :
			#	view.run_command('auto_complete', {'disable_auto_insert': True})


class HaxeRestartServer( sublime_plugin.WindowCommand ):

	def run( self ) :
		view = sublime.active_window().active_view()
		haxe.haxe_complete.HaxeComplete.instance().stop_server()
		haxe.haxe_complete.HaxeComplete.instance().start_server( view )

