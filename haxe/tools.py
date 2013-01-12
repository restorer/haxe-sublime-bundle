
from haxe.config import Config


import sublime
import os
import shutil

Const = Config

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

	