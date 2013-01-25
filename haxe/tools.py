
from haxe.config import Config


import sublime
import os
import shutil


import time

Const = Config


class Cache:
	def __init__ (self, cache_time = -1 ):
		self.data = {}
		self.cache_time = cache_time
		self.time_driven = cache_time != -1


	def insert (self, id, value):
		self.data[id] = (time.time(), value)

	def exists (self, id):
		return self.get_or_default(id, None) != None
	
	def get_or_insert (self, id, creator):
		res = None
		if id in self.data:
			res = self._get_val(id)
		else:
			res = creator()
			self.insert(id, res)
		return res

	def _get_val (self, id):
		return self.data[id][1]

	def _cache_invalid (self, id):
		return not self._cache_valid(id)

	def _cache_valid (self, id):
		now = time.time()
		return now - self.data[id][0] <= self.cache_time

	def get_or_default (self, id, default = None):
		res = default
		if id in self.data:
			if self.time_driven and self._cache_invalid(id):
				del self.data[id]
			else:
				res = self._get_val(id)
		return res




	def get_and_delete (self, id, default=None):
		val = default
		if id in self.data:
			if not self.time_driven or self._cache_valid(id):
				val = self._get_val(id)
			del self.data[id]
		return val

	def delete (self, id):
		if (id in self.data):
			del self.data[id]

class PathTools:

	@staticmethod
	def removeDir(path):
		
		if os.path.isdir(path):
			shutil.rmtree(path)

class SublimeTools:

	@staticmethod
	def find_view_by_name (name):
		windows = sublime.windows()
		for w in windows:
			views = w.views()
			for v in views:
				if (v.name() == name):
					return v
		return None

class ViewTools ():

	@staticmethod
	def create_missing_folders(view):
		fn = view.file_name()
		path = os.path.dirname( fn )
		if not os.path.isdir( path ) :
			os.makedirs( path )


	@staticmethod
	def get_content (view):
		return view.substr(sublime.Region(0, view.size()))

	@staticmethod
	def is_hxsl (view):
		return view.file_name().endswith(Const.HXSL_SUFFIX)

	@staticmethod
	def is_supported (view):
		return view.score_selector(0,Const.SOURCE_HAXE+','+Const.SOURCE_HXML+','+Const.SOURCE_ERAZOR+','+Const.SOURCE_NMML) > 0

	@staticmethod
	def is_unsupported (view):
		return not ViewTools.is_supported(view)

	@staticmethod
	def get_scopes_at (view, pos):
		return view.scope_name(pos).split()

	@staticmethod
	def is_haxe(view):
		return view.score_selector(0,Const.SOURCE_HAXE) > 0

	@staticmethod
	def is_hxml(view):
		return view.score_selector(0,Const.SOURCE_HXML) > 0

	@staticmethod
	def is_erazor(view):
		return view.score_selector(0,Const.SOURCE_ERAZOR) > 0

	@staticmethod
	def is_nmml(view):
		return view.score_selector(0,Const.SOURCE_NMML) > 0

	@staticmethod
	def replace_content (view, new_content):
		view.set_read_only(False)
		edit = view.begin_edit()
		view.replace(edit, sublime.Region(0, view.size()), new_content)
		view.end_edit(edit)


class ScopeTools:
	@staticmethod
	def contains_any (scopes, scopes_test):
		
		for s in scopes : 
			if s.split(".")[0] in scopes_test : 
				return True

		return False

	@staticmethod
	def contains_string_or_comment (scopes):
		return ScopeTools.contains_any(scopes, ["string", "comments"])

	
class CaretTools:
	@staticmethod
	def in_haxe_code (view, caret):
		return view.score_selector(caret,"source.haxe") > 0 and view.score_selector(caret,"string") == 0 and view.score_selector(caret,"comment") == 0

	@staticmethod
	def in_haxe_string (view, caret):
		return view.score_selector(caret,"source.haxe") > 0 and view.score_selector(caret,"string") > 0

	@staticmethod
	def in_haxe_comments (view, caret):
		return view.score_selector(caret,"source.haxe") > 0 and view.score_selector(caret,"comment") > 0		

	