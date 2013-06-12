import sublime, sublime_plugin

from datetime import datetime

from haxe.plugin import is_st3


import haxe.tools.view as viewtools
import haxe.settings as hxsettings
from haxe.tools.cache import Cache

def _haxe_file_regex():
	from haxe.project import haxe_file_regex
	return "^[0-9]{2}:[0-9]{2}:[0-9]{2}[ ]Error:[ ]" + haxe_file_regex[1:]


def timestamp_msg (msg):
	return datetime.now().strftime("%H:%M:%S") + " " + msg;



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
			
		

		self.output_view.settings().set("result_file_regex", _haxe_file_regex())
		# force result buffer
		win.get_output_panel("haxe")
		
		panel = self.output_view
			
		text = timestamp_msg(text);

		
			
		
		win.run_command("show_panel",{"panel":"output.haxe"})
		
		def do_edit(v, edit):
			region = sublime.Region(v.size(),v.size() + len(text))
			v.insert(edit, v.size(), text)
			v.end_edit( edit )
			
			if scope is not None :
				icon = "dot"
				key = "haxe-" + scope
				regions = v.get_regions( key );
				regions.append(region)
				v.add_regions( key , regions , scope , icon )

			# set seletion to the begin of the document, allows navigating
			# through errors from the start
			v.sel().clear()
			v.sel().add(sublime.Region(0))

			region = sublime.Region(v.size()+1000, v.size()+1000)
			sublime.set_timeout(lambda:v.show(region), 800)
		
		
		viewtools.async_edit(panel, do_edit)

		return panel

	def writeln (self, msg, scope = None):
		if valid_message(msg):
			self.write(msg + "\n", scope)

	def status (self, title, msg):
		if valid_message(msg):
			self.writeln(title + ": " + msg)



def make_tab_panel (win, name, syntax):
	active = win.active_view()
	v = win.new_file()
	v.set_name(name)
	#v.set_read_only(True)
	v.settings().set('word_wrap', True)
	
	v.settings().set("result_file_regex", _haxe_file_regex())
	#v.settings().set("result_line_regex", _haxe_file_regex())
	v.settings().set("haxe_panel_win_id", win.id())
	v.set_scratch(True)
	v.set_syntax_file(syntax)
	# always create the output panels on the last group (nicer)
	last_group = win.num_groups()-1
	win.set_view_index(v, last_group, 0)
	# restore old focus
	win.focus_view(active)
	return v

def valid_message (msg):
	return msg != None and msg != "" and msg != "\n"

class TabPanel():
	

	def __init__ (self, win, panel_name = "Haxe Output", panel_syntax = "Packages/Haxe/Haxe.tmLanguage"):
		self.win = win
		self.output_view = None
		self.output_view_id = None
		self.all = []
		self.panel_name = panel_name
		self.panel_syntax = panel_syntax

	
	def write (self, msg):
		
		def f () : 
			self.all = self.all[0:300]
			msg1 = timestamp_msg(msg)
			if valid_message(msg):
				self.all.insert(0,msg1)

				v = self.output_view

				if (v == None): 
					v = viewtools.find_view_by_name(self.panel_name)
					
					if (v == None):
						v = make_tab_panel(self.win, self.panel_name, self.panel_syntax)
						viewtools.replace_content(v, "".join(self.all))

					self.output_view = v
					self.output_view_id = v.id()

				if (v != None):
					def do_edit(v, edit):
						v.insert(edit, 0, msg1)
						v.end_edit( edit )
					viewtools.async_edit(v, do_edit)
					

		sublime.set_timeout(f,40)

	
	def writeln (self, msg):
		self.write(msg + "\n")

	
	def status (self, title, msg):
		if valid_message(msg):
			self.writeln(title + ": " + msg)




class PanelCloseListener (sublime_plugin.EventListener):
	def on_close(self, view):
		win = view.window()
		if (win == None):
			win = sublime.active_window();
		
		win_id = win.id()
		view_id = view.id()

		if win_id in _slide_panel:
			panel = slide_panel(win)
			if panel.output_view != None and view_id == panel.output_view.id():
				panel.output_view = None

		panel_win_id = view.settings().get("haxe_panel_win_id")
		if (panel_win_id != None):
			for p in [_tab_panel, _debug_panel]:
				panel = p.get_or_default(panel_win_id, None)
				if panel != None and panel.output_view != None and view_id == panel.output_view_id:
					print("panel safely removed")
					panel.output_view = None
					panel.output_view_id = None



_tab_panel = Cache()

def tab_panel(win = None):
	if (win is None):
		win = sublime.active_window()
	
	return _tab_panel.get_or_insert(win.id(), lambda: TabPanel(win, panel_name="Haxe Output"))

_debug_panel = Cache()


def debug_panel(win = None):
	if (win is None):
		win = sublime.active_window()
	return _debug_panel.get_or_insert(win.id(), lambda: TabPanel(win, "Haxe Plugin Debug Panel"))

_slide_panel = {}

def __slide_panel(win = None):
	return tab_panel(win)

def default_panel(win = None):
	if hxsettings.use_slide_panel():
		return slide_panel(win)
	else:
		return tab_panel(win)

def slide_panel(win = None):
	
	if (win is None):
		win = sublime.active_window()
	
	win_id = win.id()

	if (win_id not in _slide_panel):
		_slide_panel[win_id] = SlidePanel(win)
	return _slide_panel[win_id]



