import sublime
import re

from haxe import panel as hxpanel
from haxe.tools import hxsrctools

from haxe.log import log

def generate_using (view, edit):
	p = HaxeImportGenerator(hxpanel.default_panel(), view)
	return p.generate_statement(edit, "using", hxsrctools.using_line)

def generate_import (view, edit):
	p = HaxeImportGenerator(hxpanel.default_panel(), view)
	return p.generate_statement(edit, "import", hxsrctools.import_line)

# TODO clean up this class, it's really dirty

class HaxeImportGenerator:

	def __init__ (self, panel, view):
		log( "construct")
		self.view = view
		log(str(self.view))
		self.panel = panel
		self.start = None	
		self.size = None
		self.cname = None 
		
	def _get_end( self, src, offset ) :
		end = len(src)
		while offset < end:
			c = src[offset]
			offset += 1
			if not hxsrctools.word_chars.match(c): break
		return offset - 1

	def _get_start( self, src, offset ) :
		found_word = 0
		offset -= 1
		while offset > 0:
			c = src[offset]
			offset -= 1
			if found_word == 0:
				if hxsrctools.space_chars.match(c): continue
				found_word = 1
			if not hxsrctools.word_chars.match(c): break

		return offset + 2
	
	def _is_membername( self, token ) :
		return token[0] >= "Z" or token == token.upper()

	# def is_module( self , token ) :
	# 	return re.search("[\.^][A-Z]+", token);

	def _get_classname( self, view, src ) :
		loc = view.sel()[0]
		end = max(loc.a, loc.b)
		self.size = loc.size()
		if self.size == 0:
			end = self._get_end(src, end)
			self.start = self._get_start(src, end)
			self.size = end - self.start
		else:
			self.start = end - self.size

		self.cname = view.substr(sublime.Region(self.start, end)).rpartition(".")

		while (not self.cname[0] == "" and self._is_membername(self.cname[2])):
			self.size -= 1 + len(self.cname[2])
			self.cname = self.cname[0].rpartition(".")

		return self.cname

	def _compact_classname( self, edit, view ) :
		view.replace(edit, sublime.Region(self.start, self.start+self.size), self.cname[2])
		view.sel().clear()
		loc = self.start + len(self.cname[2])
		view.sel().add(sublime.Region(loc, loc))

	def _get_indent( self, src, index ) :
	
		if src[index] == "\n": return index + 1
		return index

	def _insert_statement( self, edit, view, src, statement, regex) :
		cname = "".join(self.cname)
		clow = cname.lower()
		last = None

		for imp in regex.finditer(src):
			if clow < imp.group(2).lower():
				ins = "{0}{1} {2};\n".format(imp.group(1), statement, cname)
				view.insert(edit, self._get_indent(src, imp.start(0)), ins)
				return
			last = imp

		if not last is None:
			ins = ";\n{0}{1} {2}".format(last.group(1), statement, cname)
			view.insert(edit, last.end(2), ins)
		else:
			pkg = hxsrctools.package_line.search(src)
			if not pkg is None:
				ins = "\n\n{0} {1};".format(statement, cname)
				view.insert(edit, pkg.end(0), ins)
			else:
				ins = "{0} {1};\n\n".format(statement, cname)
				view.insert(edit, 0, ins)


	def generate_statement( self , edit, statement, regex ) :
		
		view = self.view
		src = view.substr(sublime.Region(0, view.size()))
		cname = self._get_classname(view, src)
		
		if cname[1] == "" and statement == "import":
			sublime.status_message("Nothing to " + statement)
			self.panel.writeln("Nothing to " + statement)
			return

		self._compact_classname(edit, view)

		if re.search((statement + "\s+{0};").format("".join(cname)), src):
			info = "imported" if statement == "import" else "used"
			sublime.status_message("Already " + info)
			self.panel.writeln("Already " + info)
			return 
		 
		self._insert_statement(edit, view, src, statement, regex)	
