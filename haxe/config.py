

target_packages = ["flash","flash8","neko","js","php","cpp","cs","java", "sys"]

targets = ["js","cpp","swf8","swf","neko","php","java","cs", "as3"]

target_std_packages = {
	"js" : ["js"],
	"cpp" : ["cpp", "sys"],
	"neko" : ["neko", "sys"],
	"php" : ["php", "sys"],
	"java" : ["java", "sys"],
	"cs" : ["cs", "sys"],
	"swf" : ["flash"],
    "as3" : ["flash"],
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
    def __init__(self, name, plattform, args):
        self.name = name
        self.plattform = plattform
        self.args = args
        

class OpenFlTarget:
    def __init__(self, name, plattform, args):
        self.name = name
        self.plattform = plattform
        self.args = args
        


nme_targets = [
    
    NmeTarget("Flash - build only",                "flash",      ["-debug"]),
    NmeTarget("HTML5 - build only",                "html5",      ["-debug"]),
    NmeTarget("C++ - build only",                  "cpp",        ["-debug"]),
    NmeTarget("Windows - build only",              "windows",    ["-debug"]),
    NmeTarget("Mac - build only",                  "mac",        ["-debug"]),
    NmeTarget("Linux - build only",                "linux",      ["-debug"]),
    NmeTarget("Linux 64 - build only",             "linux",      ["-64 -debug"]),
    NmeTarget("iOs - test in iPhone simulator",    "ios",        ["-simulator -debug"]),
    NmeTarget("iOs - test in iPad simulator",      "ios",        ["-simulator -ipad -debug"]),
    NmeTarget("iOs - update XCode project",        "ios",        ["-ipad -debug"]),
    NmeTarget("Neko - build only",                "neko",   ["-debug"]),
    NmeTarget("Neko 64 - build only",             "neko",    ["-64 -debug"]),
    NmeTarget("WebOs - build only",             "webos",     ["-debug"]),
    NmeTarget("BlackBerry - build only",             "blackberry",   ["-debug"]),
    NmeTarget("Android - build only",             "android",   ["-debug"])
]   

openfl_targets = [
    
    OpenFlTarget("Flash - build only",                "flash",          ["-debug"]),
    OpenFlTarget("HTML5 - build only",                "html5",          ["-debug"]),
    OpenFlTarget("C++ - build only",                  "cpp",           ["-debug"]),
    OpenFlTarget("Windows - build only",              "windows",       ["-debug"]),
    OpenFlTarget("Mac - build only",                  "mac",       ["-debug"]),
    OpenFlTarget("Linux - build only",                "linux",       ["-debug"]),
    OpenFlTarget("Linux 64 - build only",             "linux",        ["-64 -debug"]),
    OpenFlTarget("iOs - test in iPhone simulator",    "ios",         ["-simulator -debug"]),
    OpenFlTarget("iOs - test in iPad simulator",      "ios",         ["-simulator -ipad -debug"]),
    OpenFlTarget("iOs - update XCode project",        "ios",        ["-ipad -debug"]),
    OpenFlTarget("Neko - build only",                "neko",        ["-debug"]),
    OpenFlTarget("Neko 64 - build only",             "neko",         ["-64 -debug"]),
    OpenFlTarget("Emscripten - build only",             "emscripten",   ["-debug"]),    
    OpenFlTarget("WebOs - build only",             "webos",     ["-debug"]),
    OpenFlTarget("BlackBerry - build only",             "blackberry",    ["-debug"]),
    OpenFlTarget("Android - build only",             "android",     ["-debug"])
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