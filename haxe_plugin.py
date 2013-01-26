import re
import sys
import traceback

import os
import sublime
import sublime_plugin

import haxe
import haxe.tools.cache
import haxe.tools.path
import haxe.tools.scope
import haxe.tools.view
import haxe.execute
import haxe.hxtools



print "start haxe_plugin"

# thx to wbond for the dynamic loading technique

reloading = {
    'happening': False,
    'shown': False
}
 

reload_mods = []

hook_match = re.search("<class '(\w+).ExcepthookChain1'>", str(sys.excepthook))

for mod in sys.modules:
    if (mod[0:5] == 'haxe.' or mod == 'haxe') and sys.modules[mod] != None:
        reload_mods.append(mod)
        reloading['happening'] = True
 

# Prevent popups during reload, saving the callbacks for re-adding later
if reload_mods:
    old_callbacks = {}
    hook_match = re.search("<class '(\w+).ExcepthookChain1'>", str(sys.excepthook))
    if hook_match: 
        _temp = __import__(hook_match.group(1), globals(), locals(),
            ['ExcepthookChain1'], -1) 
        ExcepthookChain1 = _temp.ExcepthookChain1
        old_callbacks = ExcepthookChain1.names
    sys.excepthook = sys.__excepthook__
 
mods_load_order = [
     'haxe.config'
    ,'haxe.project'
    ,'haxe.build'
    ,'haxe.complete'
    ,'haxe.typegen'
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


print "reload modules"
print str(reload_mods)
for mod in mods_load_order:
    if mod in reload_mods:
        reload(sys.modules[mod])

        
import haxe
import haxe.config
from haxe.compiler.server import Server
from haxe.build import HaxeBuild
from haxe.project import Project

from haxe.complete import (
     HaxeCompleteListener
    ,CompletionContext
) 
from haxe.commands import  ( 
     HaxeGetTypeOfExprCommand
    ,HaxeDisplayCompletion
    ,HaxeDisplayMacroCompletion
    ,HaxeInsertCompletionCommand
    ,HaxeSaveAllAndBuildCommand
    ,HaxeRunBuildCommand
    ,HaxeSelectBuildCommand 
    ,HaxeHintCommand 
    ,HaxeRestartServerCommand
    ,HaxeGenerateUsingCommand
    ,HaxeGenerateImportCommand
)

from haxe.panel import (
     PanelCloseListener
    ,TabPanel
    ,SlidePanel
)
import haxe.temp



if not hook_match:
    class ExcepthookChain1(object):
        callbacks = []
        names = {}

        @classmethod
        def add(cls, name, callback):
            if name == 'sys.excepthook':
                if name in cls.names:
                    return
                cls.callbacks.append(callback)
            else:
                if name in cls.names:
                    cls.callbacks.remove(cls.names[name])
                cls.callbacks.insert(0, callback)
            cls.names[name] = callback

        @classmethod
        def hook(cls, type, value, tb):
            for callback in cls.callbacks:
                callback(type, value, tb)

        @classmethod
        def remove(cls, name):
            if name not in cls.names:
                return
            callback = cls.names[name]
            del cls.names[name]
            cls.callbacks.remove(callback)
else:
    _temp = __import__(hook_match.group(1), globals(), locals(),
        ['ExcepthookChain1'], -1)
    ExcepthookChain1 = _temp.ExcepthookChain1




# Override default uncaught exception handler

ExcepthookChain1.add('sys.excepthook', sys.__excepthook__)


# Override default uncaught exception handler
def haxe_uncaught_except(type, value, tb):
    message = ''.join(traceback.format_exception(type, value, tb))

    if message.find('/haxe/') != -1 or message.find('\\haxe\\') != -1:
        def append_log():
            log_file_path = os.path.join(sublime.packages_path(), 'User',
                'Haxe.errors.log')
            send_log_path = log_file_path
            
            sublime.error_message(('%s: An unexpected error occurred, ' +
                'please send the file %s to support@frabbit.de') % ('Haxe',
                send_log_path))
        if reloading['happening']:
            if not reloading['shown']:
                sublime.error_message('Haxe: Sublime Haxe was just upgraded' +
                    ', please restart Sublime to finish the upgrade')
                reloading['shown'] = True
        else:
            sublime.set_timeout(append_log, 10)

if reload_mods and old_callbacks:
    for name in old_callbacks:
        ExcepthookChain1.add(name, old_callbacks[name])

ExcepthookChain1.add('sys.excepthook', sys.__excepthook__)
ExcepthookChain1.add('haxe_uncaught_except', haxe_uncaught_except)

if sys.excepthook != ExcepthookChain1.hook:
    sys.excepthook = ExcepthookChain1.hook


def unload_handler(): 
    
    ExcepthookChain1.remove('haxe_uncaught_except')

 




f = os.path.dirname(os.path.realpath(__file__))
def plugin_dir():
    return f

class HaxeDoNothingCommand( sublime_plugin.TextCommand ):
    def run( self , edit ) :
        self 
 

print "fin haxe_plugin"   