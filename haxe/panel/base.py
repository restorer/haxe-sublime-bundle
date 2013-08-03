import sublime, sublime_plugin

from haxe import settings

from haxe.tools.cache import Cache
from haxe.log import log

from haxe.panel.slidepanel import SlidePanel
from haxe.panel.tabpanel import TabPanel

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
					log("panel safely removed")
					panel.output_view = None
					panel.output_view_id = None



_tab_panel = Cache()
_debug_panel = Cache()
_slide_panel = {}

def tab_panel(win = None):
	if (win is None):
		win = sublime.active_window()
	
	return _tab_panel.get_or_insert(win.id(), lambda: TabPanel(win, panel_name="Haxe Output"))

def debug_panel(win = None):
	
	if (win is None):
		win = sublime.active_window()
	return _debug_panel.get_or_insert(win.id(), lambda: TabPanel(win, "Haxe Plugin Debug Panel"))

def __slide_panel(win = None):
	return tab_panel(win)

def default_panel(win = None):
	if settings.use_slide_panel():
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
