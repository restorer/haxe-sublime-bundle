import sublime_plugin



import sublime

from haxe.log import log
from haxe import project as hxproject

from haxe.tools import viewtools

#shared between FindDelaration Command and Listener
find_decl_file = None
find_decl_pos = None
init_text = ""
is_open = False

class HaxeGotoBuildTypesCommand( sublime_plugin.TextCommand ):
    def run( self , edit ) :
        log("run HaxeListBuildTypeCommand")

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


        bundle_list = [[k, filtered_types[k].file] for k in filtered_types]
        bundle_list_data = [(k,filtered_types[k]) for k in filtered_types]

        

        
        self.selecting_build = True
        sublime.status_message("Please select a type")
        
        win = view.window()


        global is_open, init_text

        sel = view.sel()

        if len(sel) == 1 and sel[0].begin() != sel[0].end():
            init_text = viewtools.get_content(view)[sel[0].begin():sel[0].end()]
        elif len(sel) == 1:
            reg = view.word(sel[0].begin())
            init_text = viewtools.get_content(view)[reg.begin():reg.end()]
        

        
        def on_selected (i):
            global find_decl_pos, find_decl_file, is_open, init_text
            is_open = False
            init_text = ""
            if i >= 0:
                
                selected_type = bundle_list_data[i]
                log("selected type:" + str(selected_type))
                log("selected type[0]: " + str(selected_type[0]))
                log("selected type[1]: " + str(selected_type[1]))


                src_pos = selected_type[1].src_pos
                find_decl_file = selected_type[1].file
                log("find_decl_file: " + str(find_decl_file))
                if src_pos is not None:
                    

                    find_decl_pos = src_pos
                    log("src_pos" + str(src_pos) )
                else:
                    find_decl_pos = 0


                def show():
                    win.open_file(selected_type[1].file)
                sublime.set_timeout(show, 130)
            




        is_open = True       
        win.show_quick_panel( bundle_list , on_selected  , sublime.MONOSPACE_FONT )
        #get quickpanel





class HaxeGotoBuildTypesListener(sublime_plugin.EventListener):

    def on_activated(self, view):
        
        
        
        global find_decl_pos, find_decl_file, is_open, init_text
        find_pos = find_decl_pos
        find_file = find_decl_file
        log("HaxeListBuildTypesListener::on_activated")
        
        
        log(str(view))

        
        if view != None and is_open:
            is_open = False

            viewtools.insert_at_cursor(view, init_text)
            init_text = ""
                        

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
                find_decl_file = None
                find_decl_pos = None

        
        