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

from haxe import panel

from haxe.log import log

plugin_path = plugin_base_dir()

# TODO cleanup this module

def get_word_at(view, src, pos):
    word = view.word(pos)

    word_start = word.a
    word_end = word.b

    word_str = src[word_start:word_end]

    return word_str, word_start, word_end


def prepare_build(view, project, use_display, new_src):
    build = project.get_build(view).copy()
    build.args.append(("-D", "no-inline"))

    temp_path, temp_file = hxtemp.create_temp_path_and_file(build, view.file_name(), new_src)

    build.add_classpath(temp_path)

    build.add_classpath(os.path.join(plugin_path, "haxetools"))
    
    build.add_arg(("-dce", "no"))

    if use_display:
        build.set_auto_completion(temp_file + "@0", False)

    return build, temp_path, temp_file


class HaxeFindDeclarationCommand( sublime_plugin.TextCommand ):


    def run( self , edit ) :
        self.run1(True)

    def helper_method(self):
        return "hxsublime.FindDeclaration.__sublimeFindDecl"


    def run1 (self, use_display, order = 1):
        log("run HaxeFindDeclarationCommand")
        view = self.view

        file_name = view.file_name()

        if file_name == None:
            return

        project = hxproject.current_project(view)
        

        if not project.has_build():
            project.extract_build_args(view, False)

        if not project.has_build():
            project.extract_build_args(view, True)            
            return



        helper_method = self.helper_method()
        
        src = viewtools.get_content(view)

        file_name = os.path.basename(view.file_name())

        package_match = re.match(hxsrctools.package_line, src)

        using_pos = 0 if package_match == None else package_match.end(0)

        using_insert = "using hxsublime.FindDeclaration;"

        src_before_using = src[0: using_pos]
        src_after_using = src[using_pos:]



        
        sel = view.sel()[0]
        pos = sel.begin()

        if (sel.end() == pos):

            word_str, word_start, word_end = get_word_at(view, src, pos)


            chars = ["{", "+", "-", "(", "[", "*", "/", "=", ";", ":"]
            res = hxsrctools.reverse_search_next_char_on_same_nesting_level(src, chars, word_end-1);
            
            res = hxsrctools.skip_whitespace_or_comments(src, res[0]+1)



            expr_end = word_end
            expr_start = res[0]
        else:
            expr_start = pos
            expr_end = sel.end()
        
        src_before_expr = src[using_pos:expr_start]

        src_after_expr = src[expr_end:]

        expr_string = src[expr_start:expr_end];


        display_str = ".|" if use_display else ""

        insert_before = helper_method + "("


        order_str = str(order)
        insert_after = ", " + order_str + ")" + display_str


        new_src = src_before_using + using_insert + src_before_expr + insert_before +  expr_string + insert_after + src_after_expr
        
        log(new_src)

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
                    log("nothing found (1), cannot find declaration")
                    if order == 1 and use_display:
                        self.run1(True, 2)    
                    elif order == 2 and use_display:
                        self.run1(True, 3)    
                else:
                    self.handle_successfull_result(view, json_res, using_insert, insert_before, insert_after, expr_end, build, temp_path, temp_file)
            else:
                if order == 1 and use_display:
                    self.run1(True, 2)
                elif order == 2 and use_display:
                    self.run1(True, 3)
                elif use_display:
                    log("nothing found yet (2), try again without display (workaround)")
                    self.run1(False)
                else:
                    panel.default_panel().writeln("Cannot find declaration for expression " + expr_string.strip())
                    log("nothing found (3), cannot find declaration")    

        build.run(project, view, False, cb)


    def handle_successfull_result(self, view, json_res, using_insert, insert_before, insert_after, expr_end, build, temp_path, temp_file):
        file = json_res["file"]
        min = json_res["min"]
        max = json_res["max"]

        #abs_path = abs_path.replace(build.get_relative_path(temp_file), build.get_relative_path(view.file_name())
        
        abs_path = pathtools.join_norm(build.get_build_folder(), file)
        abs_path_temp = pathtools.join_norm(build.get_build_folder(), build.get_relative_path(os.path.join(temp_path, temp_file)))


        if (abs_path == temp_file):
            if min > expr_end:
                min -= len(insert_after)
                min -= len(insert_before)
            min -= len(using_insert)
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

