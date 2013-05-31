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


class NmeTarget:
    def __init__(self, name, target, build_command, args, hxml_name):
        self.name = name
        self.target = target
        self.build_command = build_command
        self.args = args
        self.hxml_name = hxml_name

nme_targets = [
    NmeTarget("Flash - test", "flash", "test", ["-debug"], "_nme__flash.hxml"),
    NmeTarget("HTML5 - test", "html5", "test", ["-debug"], "_nme__html5.hxml")
]

# nme_targets = [
#     ("Flash - test","flash -debug","test"),
#     ("Flash - build only","flash -debug","build"),
#     ("HTML5 - test","html5 -debug","test"),
#     ("HTML5 - build only","html5 -debug","build"),
#     ("C++ - test","cpp -debug","test"),
#     ("C++ - build only","cpp -debug","build"),
#     ("Linux - test","linux -debug","test"), 
#     ("Linux - build only","linux -debug","build"), 
#     ("Linux 64 - test","linux -64 -debug","test"),
#     ("Linux 64 - build only","linux -64 -debug","build"),
#     ("iOS - test in iPhone simulator","ios -simulator -debug","test"),
#     ("iOS - test in iPad simulator","ios -simulator -ipad -debug","test"),
#     ("iOS - update XCode project","ios -debug","update"),
#     ("Android - test","android -debug","test"),
#     ("Android - build only","android -debug","build"),
#     ("WebOS - test", "webos -debug","test"),
#     ("WebOS - build only", "webos -debug","build"),
#     ("Neko - test","neko -debug","test"),
#     ("Neko - build only","neko -debug","build"),
#     ("Neko 64 - test","neko -64 -debug","test"),
#     ("Neko 64 - build only","neko -64 -debug","build"),
#     ("BlackBerry - test","blackberry -debug","test"),
#     ("BlackBerry - build only","blackberry -debug","build")
# ]

nme_target = nme_targets[0]


SOURCE_HAXE = 'source.haxe.2'
SOURCE_HXML = 'source.hxml'
SOURCE_NMML = 'source.nmml'
SOURCE_ERAZOR = 'source.erazor'
HXSL_SUFFIX = '.hxsl'