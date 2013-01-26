import sublime
import os

import haxe.config as hxconfig

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
	view.set_read_only(False)
	edit = view.begin_edit()
	view.replace(edit, sublime.Region(0, view.size()), new_content)
	view.end_edit(edit)

def in_haxe_code (view, caret):
	return view.score_selector(caret,"source.haxe") > 0 and view.score_selector(caret,"string") == 0 and view.score_selector(caret,"comment") == 0

def in_haxe_string (view, caret):
	return view.score_selector(caret,"source.haxe") > 0 and view.score_selector(caret,"string") > 0

def in_haxe_comments (view, caret):
	return view.score_selector(caret,"source.haxe") > 0 and view.score_selector(caret,"comment") > 0		
