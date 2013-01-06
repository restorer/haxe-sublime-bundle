import sublime, sublime_plugin


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


		#print "haxe exe: " + exe
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
	def showCompletionTimes (view = None):
		return HaxeSettings.getBool("show-completion-times", False, view)


	@staticmethod
	def haxeExec (view = None):
		return HaxeSettings.getString("haxe-exec", "haxe", view)

	@staticmethod
	def haxeLibraryPath (view = None):
		return HaxeSettings.getString("haxe-library-path", None, view)
		

	@staticmethod
	def haxeLibExec (view = None):
		return HaxeSettings.getString("haxelib-exec", "haxelib", view)
		