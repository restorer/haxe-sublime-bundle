import sublime
import os

from haxe.plugin import is_st2


def plugin_settings(): 
	return sublime.load_settings('Haxe.sublime-settings')


def get_from_settings(id, settings, plugin):
	prefix = "plugin_" if plugin else ""
	res = None
	pf = sublime.platform()
	if (settings.has(prefix + id + "_" + pf)):
		res = settings.get(prefix + id + "_" + pf)
	if res is None and settings.has(prefix + id):
		res = settings.get(prefix + id)
	return res

def get (id, view = None):
	if view is None:
		win = sublime.active_window()
		if (win is not None):
			view = sublime.active_window().active_view();

	res = None
	if view is not None:
		settings = view.settings()
		res = get_from_settings(id, settings, False)

	if res is None:
		res = get_from_settings(id, plugin_settings(), True)
		
	return res;

def get_bool (id, default, view = None):
	r = get(id, view)
	if r is None:
		return default
	else:
		if isinstance(r, bool):
			return r
		else :
			return None 


def get_int (id, default, view = None):
	r = get(id, view)
	if r is None:
		return default
	else:
		if isinstance(r, int):
			return r
		else :
			return None 


def get_string (id, default, view = None):
	r = get(id, view)
	if r is None:
		return default
	else:
		if is_st2 and isinstance(r, unicode):
			return r.decode("iso-8859-1")
		elif isinstance(r, str):
			return r
		else :
			return None

def no_fuzzy_completion (view = None):
	return get_bool("haxe_completion_no_fuzzy", False, view)

def top_level_completions_on_demand (view = None):
	return get_bool("haxe_completions_top_level_only_on_demand", False, view)

def show_only_async_completions (view = None):
	return get_bool("haxe_completions_show_only_async", True, view)

def is_async_completion (view = None):
	return get_bool("haxe_completion_async", True, view)

def get_completion_delays (view = None):
	return (
		get_int("haxe_completion_async_timing_hide", 60, view),
		get_int("haxe_completion_async_timing_show", 150, view)
	)


def show_completion_times (view = None):
	return get_bool("haxe_completion_show_times", False, view)


def haxe_exec (view = None):
	return get_string("haxe_exec", "haxe", view)

def use_haxe_servermode(view = None):
	return get_bool("haxe_use_servermode", True, view)

def use_haxe_servermode_wrapper (view = None):
	return get_bool("haxe_use_servermode_wrapper", False, view)

def haxe_sdk_path (view = None):
	return get_string("haxe_sdk_path", None, view)

def open_with_default_app(view = None):
	return get_string("haxe_open_with_default_app", None, view)

def haxe_inst_path (view = None):
	tmp = haxe_sdk_path(view)
	default = (os.path.normpath(haxe_sdk_path(view)) + os.path.sep + "haxe") if tmp != None else None
	if tmp is None and haxe_exec(view) != "haxe":
		default = (os.path.normpath(os.path.dirname(haxe_exec(view))))
		

	return get_string("haxe_inst_path", default, view)

def neko_inst_path (view = None):
	tmp = haxe_sdk_path(view)
		
	default = (os.path.normpath(haxe_sdk_path(view)) + os.path.sep + "default") if tmp != None else None
	return get_string("neko_inst_path", default, view)

def haxe_library_path (view = None):
	res = get_string("haxe_library_path", None, view)
	return res
	
def haxelib_exec (view = None):
	return get_string("haxe_haxelib_exec", "haxelib", view)
	
def smart_snippets (view = None):
	return get_bool("haxe_completion_smart_snippets", True, view)	

def smart_snippets_on_completion (view = None):
	return get_bool("haxe_completion_smart_snippets_on_completion", False, view)

def smart_snippets_just_current (view = None):
	return get_bool("haxe_completion_smart_snippets_just_current", False, view)	

def use_debug_panel (view = None):
	return get_bool("haxe_use_debug_panel", False, view)	

def check_on_save (view = None):
	return get_bool("haxe_check_on_save", True, view)

def use_slide_panel (view = None):
	return get_bool("haxe_use_slide_panel", True, view)	

def use_haxe_servermode_for_builds(view = None):
	return get_bool("haxe_use_servermode_for_builds", False, view)		

def use_offset_completion(view = None):
	return get_bool("haxe_use_offset_completion", False, view)