import sublime

from haxe.tools import viewtools

from haxe.panel import tools as paneltools

from haxe.tools.stringtools import encode_utf8,to_unicode, st2_encode_utf8, st3_encode_utf8

def make_tab_panel (win, name, syntax):
	active = win.active_view()
	v = win.new_file()
	v.set_name(name)
	#v.set_read_only(True)
	v.settings().set('word_wrap', True)
	
	v.settings().set("result_file_regex", paneltools.haxe_file_regex())
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

class TabPanel():
	
	def __init__ (self, win, panel_name = "Haxe Output", panel_syntax = "Packages/Haxe/Haxe.tmLanguage"):
		self.win = win
		self.output_view = None
		self.output_view_id = None
		self.all = []
		self.panel_name = panel_name
		self.panel_syntax = panel_syntax

	
	def write (self, msg, show_timestamp=True):
		
		def f () : 
			self.all = self.all[0:300]
			if show_timestamp:
				msg1 = paneltools.timestamp_msg(msg)
			else:
				msg1 = msg
			if paneltools.valid_message(msg):
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
						
						
						v.insert(edit, 0, st3_encode_utf8(to_unicode(msg1)))
						v.end_edit( edit )
					viewtools.async_edit(v, do_edit)
					

		sublime.set_timeout(f,40)

	
	def writeln (self, msg, show_timestamp=True):
		self.write(msg + "\n")

	
	def status (self, title, msg, show_timestamp=True):
		
		if paneltools.valid_message(msg):
			self.writeln(title + ": " + msg)
