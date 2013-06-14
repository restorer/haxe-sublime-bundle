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

from haxe.build.nmebuild import NmeBuild

class OpenFlBuild (NmeBuild):

	def __init__(self, project, title, openfl_xml, target, cb = None):
		super(OpenFlBuild, self).__init__(project, title, openfl_xml, target, cb)
		

	def copy (self):
		r = OpenFlBuild(self.project, self.title, self.nmml, self.target, self.hxml_build.copy())
		
		return r

	def _get_run_exec(self, project, view):
		return project.openfl_exec(view)

	

	def filter_platform_specific(self, packs_or_classes):
		res = []
		for c in packs_or_classes:
			# allow only flash package
			if not stringtools.startswith_any(c,["native", "browser", "nme"]):
				res.append(c)

		return res

	def get_build_command(self):
		return ["haxelib", "run", "openfl"]

	def to_string(self) :
		#out = os.path.basename(self.hxml_build.output)
		out = self.title
		return "{out} (OpenFL - {target})".format(out=out, target=self.target.name);

	def is_package_available (self, pack):
		target = self.hxml_build.target
		cls = hxconfig

		tp = list(cls.target_packages)
		tp.extend(["native", "browser", "nme"])

		no_target_pack = not pack in tp
		is_flash_pack = pack == "flash"

		available = target == None or no_target_pack or is_flash_pack

		return available
