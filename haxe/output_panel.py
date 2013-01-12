import sublime, sublime_plugin

from haxe.tools import ViewTools, SublimeTools


class Panel ():
	def __init__ (self):
		self.view = None
		self.all = []

	def on_close(self, view):
		
		if view != None and (view.id() == self.view.id()):
			self.view = None






class HaxePanel(sublime_plugin.EventListener):
	outputView = None

	all = []

	def on_close(self, view):
		
		if HaxePanel.outputView != None and (view.id() == HaxePanel.outputView.id()):
			HaxePanel.outputView = None
	
	@staticmethod
	def makePanel (name, syntax):
		v = sublime.active_window().new_file()
		v.set_name(name)
		v.set_read_only(True)
		v.set_scratch(True)
		v.set_syntax_file(syntax)
		return v


	@staticmethod
	def validMessage (msg):
		return msg != None and msg != "" and msg != "\n"

	@staticmethod
	def write (msg):
		def f () : 
			

			if HaxePanel.validMessage(msg):
				HaxePanel.all.insert(0,msg)

				v = HaxePanel.outputView

				if (v == None): 
					v = SublimeTools.find_view_by_name("Haxe Output")
					
					if (v == None):
						v = HaxePanel.makePanel("Haxe Output", "Packages/Haxe/Haxe.tmLanguage")
					
					HaxePanel.outputView = v


				if (v != None):
					ViewTools.replace_content(v, "".join(HaxePanel.all))
					v.set_read_only(True)

		sublime.set_timeout(f,1)

	@staticmethod
	def writeln (msg):
		HaxePanel.write(msg + "\n")

	@staticmethod
	def status (title, msg):
		if HaxePanel.validMessage(msg):
			HaxePanel.writeln(title + ": " + msg)