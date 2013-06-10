import sys
import sublime

print("init haxe_plugin")

is_st3 = int(sublime.version()) >= 3000

if not is_st3:
    prefix = "Haxe." if is_st3 else ""

    plugin_modules = [
         prefix + 'haxe.config'
        ,prefix + 'haxe.project'
        ,prefix + 'haxe.build'
        ,prefix + 'haxe.completion.base'
        ,prefix + 'haxe.completion.hx.base'
        ,prefix + 'haxe.completion.hx.constants'
        ,prefix + 'haxe.completion.hx.types'
        ,prefix + 'haxe.completion.hx.toplevel'
        ,prefix + 'haxe.completion.hxsl.base'
        ,prefix + 'haxe.completion.hxml.base'
        ,prefix + 'haxe.commands'
        ,prefix + 'haxe.execute'
        ,prefix + 'haxe.codegen'
        ,prefix + 'haxe.compiler.server'
        ,prefix + 'haxe.compiler.output'
        ,prefix + 'haxe.lib'
        ,prefix + 'haxe.tools.path'
        ,prefix + 'haxe.tools.view'
        ,prefix + 'haxe.tools.scope'
        ,prefix + 'haxe.tools.cache'
        ,prefix + 'haxe.tools.decorator'
        ,prefix + 'haxe.panel'
        ,prefix + 'haxe.log'
        ,prefix + 'haxe.settings'
        ,prefix + 'haxe.startup'
        ,prefix + 'haxe.temp'
        ,prefix + 'haxe.types'
        ,prefix + 'haxe.hxtools'
        ,prefix + 'haxe.plugin'
    ]

    reload_mods = []

    for mod in sys.modules:
        if (mod[0:5] == 'haxe.' or mod == 'haxe' or mod == 'Haxe' or mod[0:5] == 'Haxe.') and sys.modules[mod] != None:
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

    print("-----------------")
    print("Reloaded modules: " + mod_str(reloaded))
    print("\nImported modules: " + mod_str(imported))
    print("-----------------")


# all classes must be included manually, because sublimes autoreload does
# not reload them otherwise (at runtime)

if not is_st3:

    from haxe.compiler.server import (

        Server
    )

    from haxe.build import (

        HaxeBuild
    )

    from haxe.project import (
         ProjectListener
        ,Project
        ,ProjectCompletionContext
    )

    from haxe.completion.base import (

         CompletionListener
         
    ) 

 
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
        ,HaxeSelectBuildCommand 
        ,HaxeAsyncTriggeredCompletionCommand
        ,HaxeSaveAllAndBuildCommand
        ,HaxeSaveAllAndCheckCommand
        ,HaxeSaveAllAndRunCommand
        ,HaxeRunBuildCommand
        
        
        ,HaxeRestartServerCommand
        ,HaxeGenerateUsingCommand
        ,HaxeGenerateImportCommand
        ,HaxeCreateTypeCommand
        ,HaxeCreateTypeListener
        ,HaxeFindDeclarationCommand 
        ,HaxeExecCommand
        ,HaxeBuildOnSaveListener
        ,HaxeFindDeclarationListener
        ,HaxeInstallLibCommand
        #,HaxeSublimeTriggeredCompletionCommand
        

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
else:
    from Haxe.haxe.compiler.server import (

        Server
    )

    from Haxe.haxe.build import (

        HxmlBuild
    )

    from Haxe.haxe.project import (

         Project
        ,ProjectListener
        ,ProjectCompletionContext
    )

    from Haxe.haxe.completion.base import (

         CompletionListener
         
    ) 

    from Haxe.haxe.completion.hx.types import (

         CompletionOptions
        ,CompletionTypes
        ,TopLevelOptions
        ,CompletionSettings
        ,CompletionContext
        ,CompletionInfo
    ) 

    from Haxe.haxe.commands import (

         HaxeGetTypeOfExprCommand
        ,HaxeDisplayCompletionCommand
        ,HaxeDisplayMacroCompletionCommand
        ,HaxeHintDisplayCompletionCommand
        ,HaxeMacroHintDisplayCompletionCommand
        ,HaxeSaveAllAndBuildCommand
        ,HaxeSelectBuildCommand 
        ,HaxeAsyncTriggeredCompletionCommand
        ,HaxeRunBuildCommand
        ,HaxeSaveAllAndCheckCommand
        ,HaxeSaveAllAndRunCommand
        
        ,HaxeRestartServerCommand
        ,HaxeGenerateUsingCommand
        ,HaxeGenerateImportCommand
        ,HaxeCreateTypeCommand
        ,HaxeCreateTypeListener
        ,HaxeFindDeclarationCommand 
        ,HaxeExecCommand
        ,HaxeBuildOnSaveListener
        ,HaxeFindDeclarationListener
        ,HaxeInstallLibCommand
    ) 
    
    # only st3 relevant
    from Haxe.haxe.tools.view import (
        HaxeTextEditCommand
    )
    from Haxe.haxe.panel import (

         PanelCloseListener
        ,TabPanel
        ,SlidePanel
    )

    from Haxe.haxe.codegen import (

         HaxeImportGenerator
    )

    from Haxe.haxe.tools.cache import (
         Cache
    )

print("init haxe_plugin finished")