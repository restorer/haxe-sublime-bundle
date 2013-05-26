import sys

print "init haxe_plugin"

plugin_modules = [
     'haxe.config'
    ,'haxe.project'
    ,'haxe.build'
    ,'haxe.completion.base'
    ,'haxe.completion.hx.base'
    ,'haxe.completion.hx.constants'
    ,'haxe.completion.hx.types'
    ,'haxe.completion.hx.toplevel'
    ,'haxe.completion.hxsl.base'
    ,'haxe.completion.hxml.base'
    ,'haxe.commands'
    ,'haxe.execute'
    ,'haxe.codegen'
    ,'haxe.compiler.server'
    ,'haxe.compiler.output'
    ,'haxe.lib'
    ,'haxe.tools.path'
    ,'haxe.tools.view'
    ,'haxe.tools.scope'
    ,'haxe.tools.cache'
    ,'haxe.panel'
    ,'haxe.log'
    ,'haxe.settings'
    ,'haxe.startup'
    ,'haxe.temp'
    ,'haxe.types'
    ,'haxe.hxtools'
]

reload_mods = []

for mod in sys.modules:
    if (mod[0:5] == 'haxe.' or mod == 'haxe') and sys.modules[mod] != None:
        reload_mods.append(mod) 

reloaded = []
imported = []
for mod in plugin_modules:
    if mod in reload_mods:
        reloaded.append(mod)
        reload(sys.modules[mod])
    else:
        imported.append(mod)
        __import__(mod)

def mod_str (mods):
    return (str(len(mods)) + " modules ")  + ("\n" + ", ".join(mods) if len(mods) > 0 else "")

print "-----------------"
print "Reloaded modules: " + mod_str(reloaded)
print "\nImported modules: " + mod_str(imported)
print "-----------------"


# all classes must be included manually, because sublimes autoreload does
# not reload them otherwise (at runtime)

from haxe.compiler.server import (

    Server
)

from haxe.build import (

    HaxeBuild
)

from haxe.project import (

     Project
    ,ProjectCompletionContext
)

from haxe.completion.base import (

     HaxeCompleteListener
     
) 

#from haxe.completion.hx import

#from haxe.completion.hxsl import ()

     
     


from haxe.completion.hx.types import (

     CompletionOptions
    ,CompletionTypes
    ,TopLevelOptions
    ,CompletionSettings
    ,CompletionContext
    ,CompletionInfo
) 

from haxe.commands import (

     HaxeGetTypeOfExprCommand
    ,HaxeDisplayCompletionCommand
    ,HaxeDisplayMacroCompletionCommand
    ,HaxeHintDisplayCompletionCommand
    ,HaxeMacroHintDisplayCompletionCommand
    ,HaxeInsertCompletionCommand
    ,HaxeSaveAllAndBuildCommand
    ,HaxeRunBuildCommand
    ,HaxeRunBuildAltCommand
    ,HaxeSelectBuildCommand 
    ,HaxeRestartServerCommand
    ,HaxeGenerateUsingCommand
    ,HaxeGenerateImportCommand
    ,HaxeCreateTypeCommand
    ,HaxeCreateTypeListener
    ,HaxeFindDeclarationCommand 
    ,HaxeExecCommand
    ,HaxeBuildOnSaveListener
    ,HaxeFindDeclarationListener

) 

from haxe.panel import (

     PanelCloseListener
    ,TabPanel
    ,SlidePanel
)

from haxe.codegen import (

     HaxeImportGenerator
)

from haxe.tools.cache import (
     Cache
)

print "init haxe_plugin finished"   