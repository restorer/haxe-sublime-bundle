# -*- coding: utf-8 -*-
import sys
import sublime
import imp
import os

print("init haxe_plugin")


is_st3 = int(sublime.version()) >= 3000



#hook for imports, so that st3 imports work like st2 imports (same package structure)
if is_st3:
    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    class MyImporter:
        
        def find_module(self, fullname, path = None):
            if fullname.startswith("haxe"):
                return self
            return None

        def load_module(self, name):
            try:
                if not name in sys.modules:
                    module_info = imp.find_module(name, [base_path + "/Haxe"])
                    module = imp.load_module(name, *module_info)
                    sys.modules[name] = module
                return sys.modules[name]
            except Exception as e:
                print("cannot load module " + name + " - error: " + str(e))
                return None

    sys.meta_path.append(MyImporter())



def reload_modules():
    plugin_modules = [
         
         'haxe.build'
         ,'haxe.build.hxmlbuild'
         ,'haxe.build.nmebuild'
         ,'haxe.build.openflbuild'
         ,'haxe.build.tools'
         
         ,'haxe.commands'
         ,'haxe.commands.build'
         ,'haxe.commands.completion'
         ,'haxe.commands.completion_server'
         ,'haxe.commands.create_type'
         ,'haxe.commands.execute'
         ,'haxe.commands.find_declaration'
         ,'haxe.commands.generate_import'
         ,'haxe.commands.get_expr_type'
         ,'haxe.commands.haxelib'
         ,'haxe.commands.show_doc'

         ,'haxe.compiler'
         ,'haxe.compiler.server'
         ,'haxe.compiler.output'

         ,'haxe.completion'
         ,'haxe.completion.base'
         ,'haxe.completion.hx'
         ,'haxe.completion.hx.base'
         ,'haxe.completion.hx.constants'
         ,'haxe.completion.hx.types'
         ,'haxe.completion.hx.toplevel'
         ,'haxe.completion.hxsl'
         ,'haxe.completion.hxsl.base'
         ,'haxe.completion.hxml'
         ,'haxe.completion.hxml.base'

         ,'haxe.panel'         
         ,'haxe.panel.base'
         ,'haxe.panel.slidepanel'
         ,'haxe.panel.tabpanel'
         ,'haxe.panel.tools'

         ,'haxe.project'
         ,'haxe.project.base'
         ,'haxe.project.completion_state'
         ,'haxe.project.project'
         ,'haxe.project.tools'

         ,'haxe.tools.cache'
         ,'haxe.tools.decorator'
         ,'haxe.tools.hxsrctools'
         ,'haxe.tools.pathtools'
         ,'haxe.tools.scopetools'
         ,'haxe.tools.stringtools'
         ,'haxe.tools.sublimetools'
         ,'haxe.tools.viewtools'

         ,'haxe.codegen'
         ,'haxe.config'
         ,'haxe.execute'
         ,'haxe.haxelib'
         ,'haxe.log'
         ,'haxe.plugin'
         ,'haxe.settings'
         ,'haxe.temp'
         ,'haxe.types'
         ,'haxe'
         
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
            imp.reload(sys.modules[mod])
        else:
            imported.append(mod)
            __import__(mod)
    def mod_str (mods):
        return (str(len(mods)) + " modules ")  + ("\n" + ", ".join(mods) if len(mods) > 0 else "")
    print("-----------------")
    print("Reloaded modules: " + mod_str(reloaded))
    print("\nImported modules: " + mod_str(imported))
    print("-----------------")

sublime.set_timeout(reload_modules, 30)

# all classes must be included manually, because sublimes autoreload does
# not reload them otherwise (at runtime)



from haxe.compiler.server import (

    Server
)

from haxe.build import (

    HxmlBuild
)

from haxe.project import (
    ProjectListener
)

from haxe.completion.base import (

     CompletionListener   
) 

from haxe.panel import (

     PanelCloseListener
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
    ,HaxeShowDocCommand

) 



from haxe.codegen import (

     HaxeImportGenerator
)

from haxe.tools.viewtools import (
    HaxeTextEditCommand
)

print("init haxe_plugin finished")