import sublime



def get (id, view = None):
	if view == None:
		win = sublime.active_window()
		if (win != None):
			view = sublime.active_window().active_view();

	res = None 
	if (view != None):
		settings = view.settings()
		if settings.has("haxe"):
			s = settings.get("haxe")
			if id in s:
				v = s[id]
				res = v

	return res;


def get_bool (id, default, view = None):
	r = get(id, view)
	if (r == None):
		return default
	else:
		if isinstance(r, bool):
			return r
		else :
			return None 


def get_int (id, default, view = None):
	r = get(id, view)
	if (r == None):
		return default
	else:
		if isinstance(r, int):
			return r
		else :
			return None 


def get_string (id, default, view = None):
	r = get(id, view)
	if (r == None):
		return default
	else:
		if isinstance(r, unicode):
			return r.decode("iso-8859-1")
		elif isinstance(r, str):
			return r
		else :
			return None
		
	
def no_fuzzy_completion (view = None):
	return get_bool("no-fuzzy-completion", False, view)

def top_level_completions_on_demand (view = None):
	return get_bool("top-level-completions-on-demand", False, view)

def only_delayed_completions (view = None):
	return get_bool("only-delayed-completions", False, view)

def is_delayed_completion (view = None):
	return get_bool("delayed-completion", False, view)

def get_completion_delays (view = None):
	return (
		get_int("delayed-completion-timing-hide", 50, view),
		get_int("delayed-completion-timing-show", 170, view)
	)


def show_completion_times (view = None):
	return get_bool("show-completion-times", False, view)


def haxe_exec (view = None):
	return get_string("haxe-exec", "haxe", view)

def haxe_library_path (view = None):
	res = get_string("haxe-library-path", None, view)
	return res
	

def haxelib_exec (view = None):
	return get_string("haxelib-exec", "haxelib", view)
		