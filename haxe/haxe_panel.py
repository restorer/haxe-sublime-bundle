import sublime, sublime_plugin



class HaxePanel(sublime_plugin.EventListener):
	outputView = None

	all = []

	def on_close(self, view):
		
		if HaxePanel.outputView != None and (view.id() == HaxePanel.outputView.id()):
			HaxePanel.outputView = None
 
	@staticmethod
	def write (msg):
		def f () : 
			if msg != None and msg != "" and msg != "\n":
				HaxePanel.all.insert(0,msg)
				v = None
				v = HaxePanel.outputView

				if (v == None):  
					windows = sublime.windows()
					for w in windows:
						views = w.views()
						for v1 in views:
							if (v1.name() == "Haxe Output"):
								v = v1
					if (v == None):
						v = sublime.active_window().new_file()
					v.set_name("Haxe Output")
					v.set_read_only(True)
					v.set_scratch(True)
					HaxePanel.outputView = v
					#v.set_name("Haxe Panel")
					#v = sublime.active_window().get_output_panel("haxe")
					v.set_syntax_file("Packages/Haxe/Haxe.tmLanguage")


				if (v != None):
					v.set_read_only(False)
					edit = v.begin_edit()
					v.insert(edit, 0, "".join(HaxePanel.all))
					v.end_edit(edit)
					v.set_read_only(True)
					print "do show panel"
					#sublime.active_window().run_command("show_panel", { "panel": "output.haxe"})
		sublime.set_timeout(f,1)
			
			
				
				


	@staticmethod
	def writeln (msg):
		HaxePanel.write(msg + "\n")

	@staticmethod
	def status (title, msg):
		HaxePanel.writeln(msg)