from __future__ import absolute_import

import os
import re
import glob
import time
import codecs
import sublime
import haxe.config as hxconfig
import haxe.types as hxtypes
import haxe.lib as hxlib
import haxe.settings as hxsettings 
import haxe.tools.path as pathtools
import haxe.tools.stringtools as stringtools
import haxe.panel as hxpanel
from haxe.execute import run_cmd, run_cmd_async
from haxe.log import log

from haxe.plugin import is_st3, is_st2




class NmeBuild :

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
		display_cmd = list(self.get_build_command())
		display_cmd.append("display")
		from haxe.build.tools import create_haxe_build_from_nmml
		return create_haxe_build_from_nmml(self.project, self.target, self.nmml, display_cmd)

	@property
	def hxml_build (self):
		if self._hxml_build == None:
			self._hxml_build = self._get_hxml_build_with_nme_display()

		return self._hxml_build
	
	def to_string(self) :
		return "{title} (NME - {target})".format(title=self.title, target=self.target.name);
		
	def set_std_classes(self, std_classes):
		self.hxml_build.set_std_classes(std_classes)

	def set_std_packs(self, std_packs):
		self.hxml_build.set_std_packs(std_packs)

	def _filter_platform_specific(self, packs_or_classes):
		res = []
		for c in packs_or_classes:
			if not c.startswith("native") and not c.startswith("browser") and not c.startswith("flash") and not c.startswith("flash9") and not c.startswith("flash8"):
				res.append(c)

		return res

	def get_types(self):
		classes, packages = self.hxml_build.get_types()
		return self._filter_platform_specific(classes), self._filter_platform_specific(packages)

	@property
	def std_classes(self):
		return self._filter_platform_specific(self.hxml_build.std_classes)

	@property
	def std_packs(self):
		return self._filter_platform_specific(self.hxml_build.std_packs)

	def copy (self):
		return NmeBuild(self.project, self.title, self.nmml, self.target, self.hxml_build.copy())

	def get_relative_path(self, file):
		return self.hxml_build.get_relative_path(file)

	def get_build_folder(self):
		r = None
		if self.nmml is not None:
			r = os.path.dirname(self.nmml)
		log("build_folder: " + str(r))
		log("nmml: " + str(self.nmml))
		return r

	def set_auto_completion(self, display, macro_completion):
		self.hxml_build.set_auto_completion(display, macro_completion)

	def set_times(self):
		self.hxml_build.set_times()

	def add_define (self, define):
		self.hxml_build.add_define(define)


	def add_classpath(self, cp):
		self.hxml_build.add_classpath(cp)

	def run(self, project, view, async, on_result):
		self.hxml_build.run(project, view, async, on_result)


	def _get_run_exec(self, project, view):
		return project.nme_exec(view)

	def get_build_command(self):
		return ["haxelib", "run", "nme"]

	def prepare_check_cmd(self, project, server_mode, view):
		cmd, folder = self.prepare_build_cmd(project, server_mode, view)
		cmd.append("--no-output")
		return cmd, folder

	def prepare_build_cmd(self, project, server_mode, view):
		return self._prepare_cmd(project, server_mode, view, "build")


	def prepare_run_cmd (self, project, server_mode, view):
		return self._prepare_cmd(project, server_mode, view, "test")


	def _prepare_cmd(self, project, server_mode, view, command):
		cmd = self.get_build_command()

		cmd.append(command)
		cmd.append(self.build_file)
		cmd.append(self.target.plattform)
		cmd.extend(self.target.args)

		return (cmd, self.get_build_folder())

	def _prepare_run(self, project, view, server_mode):
		return self.hxml_build._prepare_run(project, view, server_mode)

	@property
	def classpaths (self):
		return self.hxml_build.classpaths

	@property
	def args (self):
		return self.hxml_build.args

	# checks if a toplevel package is available in the current build
	def is_package_available (self, pack):
		target = self.hxml_build.target
		cls = hxconfig

		tp = list(cls.target_packages)
		tp.extend(["native", "browser", "nme"])

		no_target_pack = not pack in tp
		is_nme_pack = pack == "nme"

		available = target == None or no_target_pack or is_nme_pack

		return available
