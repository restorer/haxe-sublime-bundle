target_packages = ["flash","flash8","neko","js","php","cpp","cs","java","nme", "sys"]

targets = ["js","cpp","swf8","swf","neko","php","java","cs"]

target_std_packages = {
	"js" : ["js"],
	"cpp" : ["cpp", "sys"],
	"neko" : ["neko", "sys"],
	"php" : ["php", "sys"],
	"java" : ["java", "sys"],
	"cs" : ["cs", "sys"],
	"swf" : ["flash"],
	"swf8" : ["flash8"],
	"nme" : ["nme"]
}

ignored_folders_list =  [".git", ".svn"]
ignored_folders = {}
for p in ignored_folders_list:
	ignored_folders[p] = True

ignored_packages_list = ["neko._std", "cpp._std", "php._std", "js._std", "flash._std"]

ignored_packages = {}
for p in ignored_packages_list:
	ignored_packages[p] = True

ignored_types = ["haxe.io.BytesData.Unsigned_char__"]

nme_targets = [("Flash","flash","test"),("HTML5","html5","test"),("C++","cpp","test"),("Linux 64","linux -64","test"),("iOS - iPhone Simulator","ios -simulator","test"),("iOS - iPad Simulator","ios -simulator -ipad","test"),("iOS - Update XCode Project","ios","update"),( "Android","android","test"),("WebOS", "webos","test"),("Neko","neko","test"),("BlackBerry","blackberry","test")]

nme_target = ("Flash","flash","test")

SOURCE_HAXE = 'source.haxe.2'
SOURCE_HXML = 'source.hxml'
SOURCE_NMML = 'source.nmml'
SOURCE_ERAZOR = 'source.erazor'
HXSL_SUFFIX = '.hxsl'