import sublime, sublime_plugin
import os
import re
import json
import codecs


from haxe import temp as hxtemp
from haxe import project as hxproject

from haxe.plugin import plugin_base_dir

from haxe.tools import viewtools
from haxe.tools import pathtools
from haxe.tools import hxsrctools

from haxe.log import log

plugin_path = plugin_base_dir()

# TODO cleanup this module

def get_word_at(view, src, pos):
    word = view.word(pos)

    word_start = word.a
    word_end = word.b

    word_str = src[word_start:word_end]

    return word_str, word_start, word_end


def get_new_src(view, inline_workaround, use_display, using_line, helper_method, word_str, add, start, end):
    if inline_workaround:
        add_x = helper_method         
        add_y = ""
        if use_display:
            add_y = ".|"
        new_src = start + add_x + "(" + word_str + ")" + add_y + end;
    else:
        new_src = start + word_str + add + end;
    package_decl = re.search(hxsrctools.package_line, new_src)

    if (package_decl == None):
        new_src = using_line + new_src
    else:
        new_src = new_src[0:package_decl.end(0)]+using_line+new_src[package_decl.end(0):len(new_src)]
    return new_src

def prepare_build(view, project, use_display, new_src):
    build = project.get_build(view).copy()
    build.args.append(("-D", "no-inline"))

    temp_path, temp_file = hxtemp.create_temp_path_and_file(build, view.file_name(), new_src)

    build.add_classpath(temp_path)

    build.add_classpath(os.path.join(plugin_path, "haxetools"))
    
    if use_display:
        build.set_auto_completion(temp_file + "@0", False)

    return build, temp_path, temp_file


class HaxeFindDeclarationCommand( sublime_plugin.TextCommand ):



    def run( self , edit ) :
        self.run1(True, False)

    def helper_method(self):
        return "__sublimeFindDecl"

    def using_class(self):
        return "hxsublime.FindDeclaration"


    def run1 (self, use_display, inline_workaround = False):
        print("run HaxeFindDeclarationCommand")
        view = self.view

        file_name = view.file_name()

        if file_name == None:
            return

        project = hxproject.current_project(view)
        

        helper_method = self.helper_method()
        
        src = viewtools.get_content(view)

        file_name = os.path.basename(view.file_name())


        using_line = "\nusing " + self.using_class() + ";\n"

        pos = view.sel()[0].a

        word_str, word_start, word_end = get_word_at(view, src, pos)

        #prev_symbol = src[word_start-1]
        
        #field_access = True if prev_symbol == "." else False
        
        added_call = "." + helper_method + "()"

        if use_display:
            added_call += ".|"

        src_before_word = src[0:word_start]

        src_after_word = src[word_end:]

        new_src = get_new_src(view, inline_workaround, use_display, using_line, helper_method, word_str, added_call, src_before_word, src_after_word)
        

        build, temp_path, temp_file = prepare_build(view, project, use_display, new_src)

        def cb (out, err):
            hxtemp.remove_path(temp_path)

            file_pos = re.compile("\|\|\|\|\|([^|]+)\|\|\|\|\|", re.I)

            res = re.search(file_pos, out)
            if res != None:
                #we've got a proper response
                json_str = res.group(1)
                json_res = json.loads(json_str)
                if "error" in json_res:
                    error = json_res["error"]
                    if (error =="inlined" and not inline_workaround):
                        # try workaround when the current method was inlined (extern inlines are forced) by the compiler
                        self.run1(use_display, True)
                    else:
                        log("nothing found (1), cannot find declaration")

                else:
                    self.handle_successfull_result(view, json_res, added_call, using_line, word_end, build, temp_path, temp_file, use_display, inline_workaround)
            else:

                if use_display:
                    log("nothing found yet (2), try again without display (workaround)")
                    self.run1(False)
                else:
                    log("nothing found (3), cannot find declaration")    

        build.run(project, view, False, cb)


    def handle_successfull_result(self, view, json_res, add, using_line, word_end, build, temp_path, temp_file, use_display, inline_workaround):
        file = json_res["file"]
        min = json_res["min"]
        max = json_res["max"]

        #abs_path = abs_path.replace(build.get_relative_path(temp_file), build.get_relative_path(view.file_name())
        
        abs_path = pathtools.join_norm(build.get_build_folder(), file)
        abs_path_temp = pathtools.join_norm(build.get_build_folder(), build.get_relative_path(os.path.join(temp_path, temp_file)))


        if (abs_path == temp_file):
            if min > word_end:
                min -= len(add)
            min -= len(using_line)
            # we have manually stored a temp file with only \n line endings
            # so we don't have to adjust the real file position and the sublime
            # text position
        else:
            f = codecs.open(abs_path, "r", "utf-8")
            real_source = f.read()
            f.close()
            # line endings could be \r\n, but sublime text has only \n after
            # opening a file, so we have to calculate the offset betweet the
            # returned position and the real position by counting all \r before min
            # should be moved to a utility function
            offset = 0
            for i in range(0,min):
                
                if real_source[i] == u"\r":
                    offset += 1
            log("offset: " + str(offset))

            min -= offset

        if (abs_path == temp_file):
            # file is active view
            abs_path = view.file_name()
            target_view = view


            log("line ending: " + str(view.settings().get("line_ending")))

            target_view.sel().clear()
            target_view.sel().add(sublime.Region(min))

            target_view.show(sublime.Region(min))
        else:
            global find_decl_pos, find_decl_file
            find_decl_file = abs_path
            find_decl_pos = min
            # open file and listen => HaxeFindDeclarationListener
            target_view = view.window().open_file(abs_path)


#shared between FindDelaration Command and Listener
find_decl_file = None
find_decl_pos = None

class HaxeFindDeclarationListener(sublime_plugin.EventListener):

    def on_activated(self, view):
        global find_decl_pos, find_decl_file

        if (view != None and view.file_name() != None):
            if (view.file_name() == find_decl_file):

                view.sel().clear()

                min = find_decl_pos

                view.sel().add(sublime.Region(min))
                # move to line is delayed, seems to work better
                # without delay the animation to the region does not work properly sometimes
                def show ():
                    view.show_at_center(sublime.Region(min))
                sublime.set_timeout(show, 70)
            find_decl_file = None
            find_decl_pos = None

