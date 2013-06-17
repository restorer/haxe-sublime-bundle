import sublime, sublime_plugin
import os

from haxe.plugin import is_st3

from haxe import config as hxconfig

class HaxeTextEditCommand (sublime_plugin.TextCommand):
    def run (self, edit, id):
        global _async_edit_dict
        if id in _async_edit_dict:
            fun = _async_edit_dict[id]
            del _async_edit_dict[id]
            fun(self.view, edit)

# convert edit operation into a async operation with a callback, use global map (cannot pass function to command)

_async_edit_id = 0
_async_edit_dict = dict()



def insert_snippet(view, snippet):
	view.run_command("insert_snippet", {
		'contents' : snippet
	})
	

def insert_at_cursor(view, txt):
	def do_edit(v, e):
		v.insert(e, get_first_cursor_pos(v), txt)
	async_edit(view, do_edit)

def async_edit(view, do_edit):
	if is_st3:
	    def start():
	        global _async_edit_id
	        global _async_edit_dict
	        id = str(_async_edit_id)
	        if _async_edit_id > 1000000:

	        	_async_edit_id = 0
	        else:
	        	_async_edit_id += 1
	        _async_edit_dict[id] = do_edit
	        view.run_command("haxe_text_edit", { "id" : id })
	        
	    sublime.set_timeout(start, 10)
	else:
		# no need for text command in st2
		def on_run():
			edit = view.begin_edit()
			do_edit(view, edit)
			view.end_edit(edit)	
		sublime.set_timeout(on_run, 10)
		

def find_view_by_name (name):
	windows = sublime.windows()
	for w in windows:
		views = w.views()
		for v in views:
			if (v.name() == name):
				return v
	return None

def create_missing_folders(view):
	fn = view.file_name()
	path = os.path.dirname( fn )
	if not os.path.isdir( path ) :
		os.makedirs( path )

def get_first_cursor_pos (view):
	return view.sel()[0].begin()

def get_content_until_first_cursor (view):
	end = get_first_cursor_pos(view)
	return get_content_until(view, end)

def get_content_until (view, end_pos):
	return view.substr(sublime.Region(0, end_pos))

def get_content (view):
	return view.substr(sublime.Region(0, view.size()))

def is_hxsl (view):
	return view.file_name().endswith(hxconfig.HXSL_SUFFIX)

def is_supported (view):
	return view.score_selector(0,hxconfig.SOURCE_HAXE+','+hxconfig.SOURCE_HXML+','+hxconfig.SOURCE_ERAZOR+','+hxconfig.SOURCE_NMML) > 0

def is_unsupported (view):
	return not is_supported(view)

def get_scopes_at (view, pos):
	return view.scope_name(pos).split()

def is_haxe(view):
	return view.score_selector(0,hxconfig.SOURCE_HAXE) > 0

def is_hxml(view):
	return view.score_selector(0,hxconfig.SOURCE_HXML) > 0

def is_erazor(view):
	return view.score_selector(0,hxconfig.SOURCE_ERAZOR) > 0

def is_nmml(view):
	return view.score_selector(0,hxconfig.SOURCE_NMML) > 0

def replace_content (view, new_content):
	def do_edit(view, edit):
		view.replace(edit, sublime.Region(0, view.size()), new_content)
		view.end_edit(edit)	

	view.set_read_only(False)
	async_edit(view, do_edit)
	
def in_haxe_code (view, caret):
	return view.score_selector(caret,"source.haxe") > 0 and view.score_selector(caret,"string") == 0 and view.score_selector(caret,"comment") == 0

def in_haxe_string (view, caret):
	return view.score_selector(caret,"source.haxe") > 0 and view.score_selector(caret,"string") > 0

def in_haxe_comments (view, caret):
	return view.score_selector(caret,"source.haxe") > 0 and view.score_selector(caret,"comment") > 0		
