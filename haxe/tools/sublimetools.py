import sublime as sub
import os
import re
import json

from haxe.log import log

from haxe.plugin import is_st3


# last time the sublime session file was updated
_last_modification_time = None
# used for caching the path of current project file
_last_project = None
# hash to store all active projects, files without project file use the "global" context

def get_project_file(win_id = None):
    if is_st3:
        #if win_id == None:
        #    win_id = sub.active_window().id()
        return sub.active_window().project_file_name()
    else:
        global _last_project
        global _last_modification_time

        log( "try getting project file")

        if win_id == None:
            win_id = sub.active_window().id()

        project = None
        reg_session = os.path.normpath(os.path.join(sub.packages_path(), "..", "Settings", "Session.sublime_session"))
        auto_save = os.path.normpath(os.path.join(sub.packages_path(), "..", "Settings", "Auto Save Session.sublime_session"))
        session = auto_save if os.path.exists(auto_save) else reg_session

        log(auto_save)
        log(reg_session)
        log(session)

        if not os.path.exists(session) or win_id == None:
            return project


        mtime = os.path.getmtime(session)

        if (_last_modification_time is not None 
            and mtime == _last_modification_time
            and _last_project != None):
            _last_modification_time = mtime
            
            return _last_project
        else:
            _last_modification_time = mtime
        try:
            with open(session, 'r') as f:
                # Tabs in strings messes things up for some reason
                j = json.JSONDecoder(strict=False).decode(f.read())
                for w in j['windows']:
                    if w['window_id'] == win_id:
                        if "workspace_name" in w:
                            if sub.platform() == "windows":
                                # Account for windows specific formatting
                                project = os.path.normpath(w["workspace_name"].lstrip("/").replace("/", ":/", 1))
                            else:
                                project = w["workspace_name"]
                            break
        except:
            pass

        # Throw out empty project names
        if project == None or re.match(".*\\.sublime-project", project) == None or not os.path.exists(project):
            project = None

        _last_project = project
        return project

