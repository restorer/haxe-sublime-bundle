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
    
    NmeTarget("Flash",                "flash",      ["-debug"]),
    NmeTarget("HTML5",                "html5",      ["-debug"]),
    NmeTarget("C++",                  "cpp",        ["-debug"]),
    NmeTarget("Windows",              "windows",    ["-debug"]),
    NmeTarget("Mac",                  "mac",        ["-debug"]),
    NmeTarget("Linux",                "linux",      ["-debug"]),
    NmeTarget("Linux 64",             "linux",      ["-64 -debug"]),
    NmeTarget("iOs - iPhone simulator",    "ios",        ["-simulator -debug"]),
    NmeTarget("iOs - iPad simulator",      "ios",        ["-simulator -ipad -debug"]),
    NmeTarget("iOs - update XCode project",        "ios",        ["-ipad -debug"]),
    NmeTarget("Neko",                "neko",   ["-debug"]),
    NmeTarget("Neko 64",             "neko",    ["-64 -debug"]),
    NmeTarget("WebOs",             "webos",     ["-debug"]),
    NmeTarget("BlackBerry",             "blackberry",   ["-debug"]),
    NmeTarget("Android",             "android",   ["-debug"])
]   

openfl_targets = [
    
    OpenFlTarget("Flash",                "flash",          ["-debug"]),
    OpenFlTarget("HTML5",                "html5",          ["-debug"]),
    OpenFlTarget("C++",                  "cpp",           ["-debug"]),
    OpenFlTarget("Windows",              "windows",       ["-debug"]),
    OpenFlTarget("Mac",                  "mac",       ["-debug"]),
    OpenFlTarget("Linux",                "linux",       ["-debug"]),
    OpenFlTarget("Linux 64",             "linux",        ["-64 -debug"]),
    OpenFlTarget("iOs - iPhone simulator",    "ios",         ["-simulator -debug"]),
    OpenFlTarget("iOs - iPad simulator",      "ios",         ["-simulator -ipad -debug"]),
    OpenFlTarget("iOs - update XCode project",        "ios",        ["-ipad -debug"]),
    OpenFlTarget("Neko",                "neko",        ["-debug"]),
    OpenFlTarget("Neko 64",             "neko",         ["-64 -debug"]),
    OpenFlTarget("Emscripten",             "emscripten",   ["-debug"]),    
    OpenFlTarget("WebOs",             "webos",     ["-debug"]),
    OpenFlTarget("BlackBerry",             "blackberry",    ["-debug"]),
    OpenFlTarget("Android",             "android",     ["-debug"])
]   



SOURCE_HAXE = 'source.haxe.2'
SOURCE_HXML = 'source.hxml'
SOURCE_NMML = 'source.nmml'
SOURCE_ERAZOR = 'source.erazor'
HXSL_SUFFIX = '.hxsl'