import sublime, sublime_plugin

from datetime import datetime

from haxe.tools import ViewTools, SublimeTools





class SlidePanel ():

	def __init__ (self, win):
		self.win = win
		self.output_view = None


	def clear(self) :
		self.output_view = self.win.get_output_panel("haxe")

	def write( self , text , scope = None ) :
		
		win = self.win

		if self.output_view is None :
			self.output_view = win.get_output_panel("haxe")

		panel = self.output_view

		text = datetime.now().strftime("%H:%M:%S") + " " + text;
		
		edit = panel.begin_edit()
		region = sublime.Region(panel.size(),panel.size() + len(text))
		panel.insert(edit, panel.size(), text)
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

	def writeln (self, msg, scope = None):
		self.write(msg + "\n", scope)

	def status (self, title, msg):
		if valid_message(msg):
			self.writeln(title + ": " + msg)



def make_tab_panel (win, name, syntax):
	v = win.new_file()
	v.set_name(name)
	v.set_read_only(True)
	v.set_scratch(True)
	v.set_syntax_file(syntax)
	return v

def valid_message (msg):
	return msg != None and msg != "" and msg != "\n"

class TabPanel():
	

	def __init__ (self, win):
		self.win = win
		self.output_view = None
		self.all = []

	
	def write (self, msg):
		
		def f () : 
		
			if valid_message(msg):
				self.all.insert(0,msg)

				v = self.output_view

				if (v == None): 
					v = SublimeTools.find_view_by_name("Haxe Output")
					
					if (v == None):
						v = make_tab_panel(self.win, "Haxe Output", "Packages/Haxe/Haxe.tmLanguage")

					self.output_view = v

				if (v != None):
					ViewTools.replace_content(v, "".join(self.all))
					v.set_read_only(True)

		sublime.set_timeout(f,1)

	
	def writeln (self, msg):
		self.write(msg + "\n")

	
	def status (self, title, msg):
		if valid_message(msg):
			self.writeln(title + ": " + msg)


class PanelCloseListener (sublime_plugin.EventListener):
	def on_close(self, view):
		win = view.active_window()
		win_id = win.id()
		view_id = view.id()
		if win_id in _slide_panel:
			panel = slide_panel(win_id)
			if panel.output_view != None and view_id == panel.output_view.id():
				print "haxe slide panel closed"
				panel.output_view = None

		if win_id in _tab_panel:
			panel = tab_panel(win_id)
			if panel.output_view != None and view_id == panel.output_view.id():
				print "haxe tab panel closed"
				panel.output_view = None


_tab_panel = {}

def tab_panel(win = None):
	global _tab_panel
	if (win is None):
		win = sublime.active_window()
	id = win.id()
	if (id not in _tab_panel):
		_tab_panel[id] = TabPanel(win)
	return _tab_panel[id]

_slide_panel = {}

def slide_panel(win = None):
	global _slide_panel
	if (win is None):
		win = sublime.active_window()
	
	id = win.id()

	if (id not in _slide_panel):
		_slide_panel[id] = SlidePanel(win)
	return _slide_panel[id]

__all__ = ["tab_panel", "slide_panel"]
