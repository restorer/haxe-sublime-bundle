from haxe import config

from haxe.tools import stringtools

from haxe.log import log

from haxe.build.nmebuild import NmeBuild

class OpenFlBuild (NmeBuild):

	def __init__(self, project, title, openfl_xml, target, cb = None):
		super(OpenFlBuild, self).__init__(project, title, openfl_xml, target, cb)
		

	def copy (self):
		hxml_copy = self.hxml_build.copy() if self._hxml_build is not None else None
		r = OpenFlBuild(self.project, self.title, self.nmml, self.target, hxml_copy)
		
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

	def to_string(self) :
		#out = os.path.basename(self.hxml_build.output)
		out = self.title
		return "{out} (OpenFL - {target})".format(out=out, target=self.target.name);

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
		is_flash_pack = pack == "flash"

		available = target == None or no_target_pack or is_flash_pack

		return available
