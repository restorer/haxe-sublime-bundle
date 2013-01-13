import sublime


class HaxeSettings:

	 

	@staticmethod 
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

	@staticmethod 
	def getBool (id, default, view = None):
		r = HaxeSettings.get(id, view)
		if (r == None):
			return default
		else:
			if isinstance(r, bool):
				return r
			else :
				return None 

	@staticmethod 
	def get_int (id, default, view = None):
		r = HaxeSettings.get(id, view)
		if (r == None):
			return default
		else:
			if isinstance(r, int):
				return r
			else :
				return None 

	@staticmethod 
	def getString (id, default, view = None):
		r = HaxeSettings.get(id, view)
		if (r == None):
			return default
		else:
			if isinstance(r, unicode):
				return r.decode("iso-8859-1")
			elif isinstance(r, str):
				return r
			else :
				return None
			
				
	
	
	
	@staticmethod
	def no_fuzzy_completion (view = None):
		return HaxeSettings.getBool("no-fuzzy-completion", False, view)

	@staticmethod
	def top_level_completions_on_demand (view = None):
		return HaxeSettings.getBool("top-level-completions-on-demand", False, view)

	@staticmethod
	def only_delayed_completions (view = None):
		return HaxeSettings.getBool("only-delayed-completions", False, view)

	@staticmethod
	def is_delayed_completion (view = None):
		return HaxeSettings.getBool("delayed-completion", False, view)

	@staticmethod
	def get_completion_delays (view = None):
		return (
			HaxeSettings.get_int("delayed-completion-timing-hide", 50, view),
			HaxeSettings.get_int("delayed-completion-timing-show", 170, view)
		)


	@staticmethod
	def showCompletionTimes (view = None):
		return HaxeSettings.getBool("show-completion-times", False, view)


	@staticmethod
	def haxeExec (view = None):
		return HaxeSettings.getString("haxe-exec", "haxe", view)

	@staticmethod
	def haxeLibraryPath (view = None):
		res = HaxeSettings.getString("haxe-library-path", None, view)
		return res
		

	@staticmethod
	def haxeLibExec (view = None):
		return HaxeSettings.getString("haxelib-exec", "haxelib", view)
		