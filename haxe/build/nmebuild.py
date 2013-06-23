import os
import sublime 
from haxe import config

from haxe.log import log

from haxe.tools.stringtools import encode_utf8

class NmeBuild(object) :

	def __init__(self, project, title, nmml, target, cb = None):
		self._title = title
		self._target = target
		self.nmml = nmml
		self._hxml_build = cb
		self.project = project

	@property
	def title(self):
		return self._title
	@property
	def build_file(self):

		return self.nmml

	@property
	def target(self):
		return self._target

	@property
	def plattform(self):
		return self._target.plattform

	def _get_hxml_build_with_nme_display(self):
		view = sublime.active_window().active_view()
		display_cmd = list(self.get_build_command(self.project, view))
		display_cmd.append("display")
		from haxe.build.tools import create_haxe_build_from_nmml
		return create_haxe_build_from_nmml(self.project, self.target, self.nmml, display_cmd)

	@property
	def hxml_build (self):
		if self._hxml_build is None:
			self._hxml_build = self._get_hxml_build_with_nme_display()
			#self._hxml_build.get_types()

		return self._hxml_build
	
	def to_string(self) :
		return "{title} (NME - {target})".format(title=self.title, target=self.target.name);
		
	def set_std_bundle(self, std_bundle):
		self.hxml_build.set_std_bundle(std_bundle)

	

	def _filter_platform_specific(self, packs_or_classes):
	 	res = []
	 	for c in packs_or_classes:
	 		if not c.startswith("native") and not c.startswith("browser") and not c.startswith("flash") and not c.startswith("flash9") and not c.startswith("flash8"):
	 			res.append(c)

	 	return res

	def get_types(self):
		bundle = self.hxml_build.get_types()
		return bundle


	@property
	def std_bundle(self):
		return self.hxml_build.std_bundle


	def add_arg(self, arg):
		self.hxml_build.add_arg(arg)


	def copy (self):
		hxml_copy = self.hxml_build.copy() if self._hxml_build is not None else None
		return NmeBuild(self.project, self.title, self.nmml, self.target, hxml_copy)

	def get_relative_path(self, file):
		return self.hxml_build.get_relative_path(file)

	def get_build_folder(self):
		r = None
		if self.nmml is not None:
			r = os.path.dirname(self.nmml)
		log("build_folder: " + encode_utf8(r))
		log("nmml: " + encode_utf8(self.nmml))
		return r

	def set_auto_completion(self, display, macro_completion):
		self.hxml_build.set_auto_completion(display, macro_completion)

	def set_times(self):
		self.hxml_build.set_times()

	def add_define (self, define):
		self.hxml_build.add_define(define)

	def add_classpath(self, cp):
		self.hxml_build.add_classpath(cp)

	def run(self, project, view, async, on_result, server_mode = None):
		self.hxml_build.run(project, view, async, on_result, server_mode)


	def _get_run_exec(self, project, view):
		return project.nme_exec(view)

	def get_build_command(self, project, view):
		return list(self._get_run_exec(project, view))

	def prepare_check_cmd(self, project, server_mode, view):
		cmd, folder = self.prepare_build_cmd(project, server_mode, view)
		cmd.append("--no-output")
		return cmd, folder

	def prepare_build_cmd(self, project, server_mode, view):
		return self._prepare_cmd(project, server_mode, view, "build")


	def prepare_run_cmd (self, project, server_mode, view):
		return self._prepare_cmd(project, server_mode, view, "test")


	def _prepare_cmd(self, project, server_mode, view, command):
		cmd = self.get_build_command(project, view)

		cmd.append(command)
		cmd.append(self.build_file)
		cmd.append(self.target.plattform)
		cmd.extend(self.target.args)

		if server_mode:
			cmd.extend(["--connect", str(project.server.get_server_port())])

		return (cmd, self.get_build_folder())

	def _prepare_run(self, project, view, server_mode):
		return self.hxml_build._prepare_run(project, view, server_mode)

	@property
	def classpaths (self):
		return self.hxml_build.classpaths

	@property
	def args (self):
		return self.hxml_build.args

	def is_type_available (self, type):
		pack = type.toplevel_pack
		return pack is None or self.is_pack_available(pack)


	def is_pack_available (self, pack):
		if pack == "":
			return True

		pack = pack.split(".")[0]
		target = self.hxml_build.target
		
		tp = list(config.target_packages)
		tp.extend(["native", "browser", "nme"])

		no_target_pack = not pack in tp
		is_nme_pack = pack == "nme"

		available = target == None or no_target_pack or is_nme_pack

		return available
