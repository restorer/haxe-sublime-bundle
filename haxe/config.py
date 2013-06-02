

target_packages = ["flash","flash8","neko","js","php","cpp","cs","java", "sys"]

targets = ["js","cpp","swf8","swf","neko","php","java","cs"]

target_std_packages = {
	"js" : ["js"],
	"cpp" : ["cpp", "sys"],
	"neko" : ["neko", "sys"],
	"php" : ["php", "sys"],
	"java" : ["java", "sys"],
	"cs" : ["cs", "sys"],
	"swf" : ["flash"],
	"swf8" : ["flash8"]
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
    def __init__(self, name, target, build_command, hxml_name, args):
        self.name = name
        self.target = target
        self.build_command = build_command
        self.args = args
        self.hxml_name = hxml_name

class OpenFlTarget:
    def __init__(self, name, target, build_command, hxml_name, args):
        self.name = name
        self.target = target
        self.build_command = build_command
        self.args = args
        self.hxml_name = hxml_name


nme_targets = [
    NmeTarget("Flash - test",                      "flash", "test",     "_nme__flash_1.hxml",     ["-debug"]),
    NmeTarget("Flash - build only",                "flash", "build",    "_nme__flash_2.hxml",     ["-debug"]),
    NmeTarget("HTML5 - test",                      "html5", "test",     "_nme__html5_1.hxml",     ["-debug"]),
    NmeTarget("HTML5 - build only",                "html5", "build",    "_nme__html5_2.hxml",     ["-debug"]),
    NmeTarget("C++ - test",                        "cpp",   "test",     "_nme__cpp1.hxml",       ["-debug"]),
    NmeTarget("C++ - build only",                  "cpp",   "build",    "_nme__cpp2.hxml",       ["-debug"]),
    NmeTarget("Windows - test",                      "windows",   "test",   "_nme__windows1.hxml",     ["-debug"]),
    NmeTarget("Windows - build only",                "windows",   "build",  "_nme__windows2.hxml",     ["-debug"]),
    NmeTarget("Mac - test",                      "mac",   "test",   "_nme__mac1.hxml",     ["-debug"]),
    NmeTarget("Mac - build only",                "mac",   "build",  "_nme__mac2.hxml",     ["-debug"]),
    NmeTarget("Linux - test",                      "linux",   "test",   "_nme__linux1.hxml",     ["-debug"]),
    NmeTarget("Linux - build only",                "linux",   "build",  "_nme__linux2.hxml",     ["-debug"]),
    NmeTarget("Linux 64 - test",                   "linux",   "test",   "_nme__linux64_1.hxml",   ["-64 -debug"]),
    NmeTarget("Linux 64 - build only",             "linux",   "build",  "_nme__linux64_2.hxml",   ["-64 -debug"]),
    NmeTarget("iOs - test in iPhone simulator",    "ios",   "test",     "_nme__ios_ipod.hxml",  ["-simulator -debug"]),
    NmeTarget("iOs - test in iPad simulator",      "ios",   "test",     "_nme__ios_ipad.hxml",  ["-simulator -ipad -debug"]),
    NmeTarget("iOs - update XCode project",        "ios",   "update",   "_nme__ios_xcode.hxml", ["-ipad -debug"]),

    NmeTarget("Neko - test",                      "neko",   "test",   "_nme__neko1.hxml",     ["-debug"]),
    NmeTarget("Neko - build only",                "neko",   "build",  "_nme__neko2.hxml",     ["-debug"]),
    NmeTarget("Neko 64 - test",                   "neko",   "test",   "_nme__neko64_1.hxml",   ["-64 -debug"]),
    NmeTarget("Neko 64 - build only",             "neko",   "build",  "_nme__neko64_2.hxml",   ["-64 -debug"]),

    NmeTarget("WebOs - test",                   "webos",   "test",   "_nme__webos1.hxml",   ["-debug"]),
    NmeTarget("WebOs - build only",             "webos",   "build",  "_nme__webos2.hxml",   ["-debug"]),

    NmeTarget("BlackBerry - test",                   "blackberry",   "test",   "_nme__blackberry1.hxml",   ["-debug"]),
    NmeTarget("BlackBerry - build only",             "blackberry",   "build",  "_nme__blackberry2.hxml",   ["-debug"]),

    NmeTarget("Android - test",                   "android",   "test",   "_nme__android1.hxml",   ["-debug"]),
    NmeTarget("Android - build only",             "android",   "build",  "_nme__android2.hxml",   ["-debug"])
]   

openfl_targets = [
    OpenFlTarget("Flash - test",                      "flash", "test",     "_openfl__flash_1.hxml",     ["-debug"]),
    OpenFlTarget("Flash - build only",                "flash", "build",    "_openfl__flash_2.hxml",     ["-debug"]),
    OpenFlTarget("HTML5 - test",                      "html5", "test",     "_openfl__html5_1.hxml",     ["-debug"]),
    OpenFlTarget("HTML5 - build only",                "html5", "build",    "_openfl__html5_2.hxml",     ["-debug"]),
    OpenFlTarget("C++ - test",                        "cpp",   "test",     "_openfl__cpp1.hxml",       ["-debug"]),
    OpenFlTarget("C++ - build only",                  "cpp",   "build",    "_openfl__cpp2.hxml",       ["-debug"]),
    OpenFlTarget("Windows - test",                      "windows",   "test",   "_openfl__windows1.hxml",     ["-debug"]),
    OpenFlTarget("Windows - build only",                "windows",   "build",  "_openfl__windows2.hxml",     ["-debug"]),
    OpenFlTarget("Mac - test",                      "mac",   "test",   "_openfl__mac1.hxml",     ["-debug"]),
    OpenFlTarget("Mac - build only",                "mac",   "build",  "_openfl__mac2.hxml",     ["-debug"]),
    OpenFlTarget("Linux - test",                      "linux",   "test",   "_openfl__linux1.hxml",     ["-debug"]),
    OpenFlTarget("Linux - build only",                "linux",   "build",  "_openfl__linux2.hxml",     ["-debug"]),
    OpenFlTarget("Linux 64 - test",                   "linux",   "test",   "_openfl__linux64_1.hxml",   ["-64 -debug"]),
    OpenFlTarget("Linux 64 - build only",             "linux",   "build",  "_openfl__linux64_2.hxml",   ["-64 -debug"]),
    OpenFlTarget("iOs - test in iPhone simulator",    "ios",   "test",     "_openfl__ios_ipod.hxml",  ["-simulator -debug"]),
    OpenFlTarget("iOs - test in iPad simulator",      "ios",   "test",     "_openfl__ios_ipad.hxml",  ["-simulator -ipad -debug"]),
    OpenFlTarget("iOs - update XCode project",        "ios",   "update",   "_openfl__ios_xcode.hxml", ["-ipad -debug"]),

    OpenFlTarget("Neko - test",                      "neko",   "test",   "_openfl__neko1.hxml",     ["-debug"]),
    OpenFlTarget("Neko - build only",                "neko",   "build",  "_openfl__neko2.hxml",     ["-debug"]),
    OpenFlTarget("Neko 64 - test",                   "neko",   "test",   "_openfl__neko64_1.hxml",   ["-64 -debug"]),
    OpenFlTarget("Neko 64 - build only",             "neko",   "build",  "_openfl__neko64_2.hxml",   ["-64 -debug"]),

    OpenFlTarget("Emscripten - test",                   "emscripten",   "test",   "_openfl__emscripten1.hxml",   ["-debug"]),
    OpenFlTarget("Emscripten - build only",             "emscripten",   "build",  "_openfl__emscripten2.hxml",   ["-debug"]),    

    OpenFlTarget("WebOs - test",                   "webos",   "test",   "_openfl__webos1.hxml",   ["-debug"]),
    OpenFlTarget("WebOs - build only",             "webos",   "build",  "_openfl__webos2.hxml",   ["-debug"]),

    OpenFlTarget("BlackBerry - test",                   "blackberry",   "test",   "_openfl__blackberry1.hxml",   ["-debug"]),
    OpenFlTarget("BlackBerry - build only",             "blackberry",   "build",  "_openfl__blackberry2.hxml",   ["-debug"]),

    OpenFlTarget("Android - test",                   "android",   "test",   "_openfl__android1.hxml",   ["-debug"]),
    OpenFlTarget("Android - build only",             "android",   "build",  "_openfl__android2.hxml",   ["-debug"])
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