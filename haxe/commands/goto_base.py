import sublime_plugin



import sublime

from haxe.log import log
from haxe import project as hxproject

from haxe.tools import viewtools

#shared between FindDelaration Command and Listener
_find_decl_file = None
_find_decl_pos = None
_init_text = ""
_is_open = False

class HaxeGotoBaseCommand( sublime_plugin.TextCommand ):

    def get_entries (self, types):
        raise Exception("abstract method")
        #return [[p.to_string() + " - " + p.kind, p.type.file] for k in types for p in types[k].all_fields_list]

    def get_data (self, types):
        raise Exception("abstract method")
        #return [(k + "." + p.name,p) for k in types for p in types[k].all_fields_list]

    def get_file(self, data_entry):
        raise Exception("abstract method")

    def get_src_pos(self, data_entry):
        raise Exception("abstract method")

    def run( self , edit ) :
        log("run HaxeListBuildFieldsCommand")

        view = self.view

        project = hxproject.current_project(view)
        

        if not project.has_build():
            project.extract_build_args(view, False)

        if not project.has_build():
            project.extract_build_args(view, True)            
            return

        build = project.get_build(view)

        bundle = build.get_types().merge(build.std_bundle)



        bundle_types = bundle.all_types_and_enum_constructors_with_info()

        filtered_types = dict()
        
        for k in bundle_types:
            t = bundle_types[k]
            if build.is_type_available(t):
                filtered_types[k] = t


        function_list = self.get_entries(filtered_types)
        function_list_data = self.get_data(filtered_types)
        

        log(str(function_list))

        log(str(len(function_list)))

        
        self.selecting_build = True
        sublime.status_message("Please select a type")
        
        win = view.window()


        global _is_open, _init_text

        sel = view.sel()

        if len(sel) == 1 and sel[0].begin() != sel[0].end():
            _init_text = viewtools.get_content(view)[sel[0].begin():sel[0].end()]
        elif len(sel) == 1:
            reg = view.word(sel[0].begin())
            _init_text = viewtools.get_content(view)[reg.begin():reg.end()]
        else:
            _init_text = ""
        


        def on_selected (i):
            global _find_decl_pos, _find_decl_file, _is_open, _init_text
            _is_open = False
            _init_text = ""
            if i >= 0:
                
                selected_type = function_list_data[i]
                log("selected field: " + str(selected_type[0]))
                
                src_pos = self.get_src_pos(selected_type[1])

                goto_file = self.get_file(selected_type[1])

                _find_decl_file = goto_file

                log("find_decl_file: " + str(_find_decl_file))
                if src_pos is not None:
                    

                    _find_decl_pos = src_pos
                    log("src_pos" + str(src_pos) )
                else:
                    _find_decl_pos = 0


                def show():
                    win.open_file(goto_file)
                sublime.set_timeout(show, 130)
                
        _is_open = True       
        win.show_quick_panel( function_list , on_selected  , sublime.MONOSPACE_FONT )
        #get quickpanel





class HaxeGotoBaseListener(sublime_plugin.EventListener):

    def on_activated(self, view):
        
        
        global _find_decl_pos, _find_decl_file, _is_open, _init_text
        find_pos = _find_decl_pos
        find_file = _find_decl_file
        log("HaxeListBuildTypesListener::on_activated")
        
        
        log(str(view))

        
        if view != None and _is_open:
            _is_open = False

            viewtools.insert_at_cursor(view, _init_text)
            _init_text = ""
                        

        if (view != None and view.file_name() != None):
            log("show at X")
            log("decl file: " + str(find_file))
            if (view.file_name() == find_file):
                log("show at Y")
                view.sel().clear()

                min = find_pos

                view.sel().add(sublime.Region(min))

                log("show at:" + str(min))
                # move to line is delayed, seems to work better
                # without delay the animation to the region does not work properly sometimes
                def show ():
                    log("show at:" + str(min))
                    view.show_at_center(sublime.Region(min))
                sublime.set_timeout(show, 100)
                _find_decl_file = None
                _find_decl_pos = None

        
        