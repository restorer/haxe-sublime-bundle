import sublime, sublime_plugin

from datetime import datetime

from haxe.tools import ViewTools, SublimeTools


class Panel ():
	def __init__ (self):
		self.view = None
		self.all = []

	def on_close(self, view):
		
		if view != None and (view.id() == self.view.id()):
			self.view = None






class NormalPanel ():

	def __init__ (self):
		self.panel = None


	def clear(self, view = None) :
		if (view == None):
			win = sublime.active_window()
		else:
			win = view.window()

		self.panel = win.get_output_panel("haxe")

	def write( self , text , view = None, scope = None ) :
		if (view == None):
			win = sublime.active_window()
		else:
			win = view.window()

		if self.panel is None :
			self.panel = win.get_output_panel("haxe")

		panel = self.panel

		text = datetime.now().strftime("%H:%M:%S") + " " + text;
		
		edit = panel.begin_edit()
		region = sublime.Region(panel.size(),panel.size() + len(text))
		panel.insert(edit, panel.size(), text + "\n")
		panel.end_edit( edit )

		if scope is not None :
			icon = "dot"
			key = "haxe-" + scope
			regions = panel.get_regions( key );
			regions.append(region)
			panel.add_regions( key , regions , scope , icon )
		#print( err )
		win.run_command("show_panel",{"panel":"output.haxe"})

		return self.panel

normal_panel = NormalPanel()

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