import sublime, sublime_plugin
import os
import re
import json
import codecs


from haxe import temp as hxtemp
from haxe import project as hxproject

from haxe.plugin import plugin_base_dir, is_st3


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


def prepare_build(view, project, new_src, display_pos):
    build = project.get_build(view).copy()
    build.args.append(("-D", "no-inline"))

    temp_path, temp_file = hxtemp.create_temp_path_and_file(build, view.file_name(), new_src)

    build.add_classpath(temp_path)

    build.add_classpath(os.path.join(plugin_path, "haxetools"))
    
    build.add_arg(("-dce", "no"))
    build.add_arg( ("-D", "display-mode=usage") )
    build.add_define("display-mode=usage")

    build.set_auto_completion(temp_file + "@" + str(display_pos), False)

    return build, temp_path, temp_file


class HaxeFindOccurencesCommand( sublime_plugin.TextCommand ):


    def run( self , edit ) :
        self.run1()

    

    def run1 (self):
        print("run HaxeFindDeclarationCommand")
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



        
        
        src = viewtools.get_content(view)

        file_name = os.path.basename(view.file_name())

        pos = view.sel()[0].a



        word_str, word_start, word_end = get_word_at(view, src, pos)


        log(word_str)
        log(str(word_start))
        log(str(word_end))

        chars = ["{", "+", "-", "(", "[", "*", "/", "=", ";", ":"]
        

        
                
        src_before_word_end = src[0:word_end]

        


        pos_str = src_before_word_end

        log(pos_str)

        if is_st3:
            s_bytes = pos_str.encode()
        else:
            s_bytes = pos_str.encode("utf-8")
        display_pos = len(s_bytes)


        #new_src = src_before_word + expr_string + insert_after + src_after_expr
        new_src = src
        log(new_src)

        build, temp_path, temp_file = prepare_build(view, project,  new_src, display_pos)

        def cb (out, err):
            hxtemp.remove_path(temp_path)

            log(out)
            log(err)

            
            # res = re.search(file_pos, out)
            # if res != None:
            #     #we've got a proper response
            #     json_str = res.group(1)
            #     json_res = json.loads(json_str)
            #     if "error" in json_res:
            #         error = json_res["error"]
            #         log("nothing found (1), cannot find declaration")
            #         if order == 1 and use_display:
            #             self.run1(True, 2)    
            #         elif order == 2 and use_display:
            #             self.run1(True, 3)    
            #     else:
            #         self.handle_successfull_result(view, json_res, using_insert, insert_before, insert_after, expr_end, build, temp_path, temp_file)
            # else:
            #     if order == 1 and use_display:
            #         self.run1(True, 2)
            #     elif order == 2 and use_display:
            #         self.run1(True, 3)
            #     elif use_display:
            #         log("nothing found yet (2), try again without display (workaround)")
            #         self.run1(False)
            #     else:
            #         log("nothing found (3), cannot find declaration")    

        build.run(project, view, False, cb, False)


    # def handle_successfull_result(self, view, json_res, using_insert, insert_before, insert_after, expr_end, build, temp_path, temp_file):
    #     file = json_res["file"]
    #     min = json_res["min"]
    #     max = json_res["max"]

    #     #abs_path = abs_path.replace(build.get_relative_path(temp_file), build.get_relative_path(view.file_name())
        
    #     abs_path = pathtools.join_norm(build.get_build_folder(), file)
    #     abs_path_temp = pathtools.join_norm(build.get_build_folder(), build.get_relative_path(os.path.join(temp_path, temp_file)))


    #     if (abs_path == temp_file):
    #         if min > expr_end:
    #             min -= len(insert_after)
    #             min -= len(insert_before)
    #         min -= len(using_insert)
    #         # we have manually stored a temp file with only \n line endings
    #         # so we don't have to adjust the real file position and the sublime
    #         # text position
    #     else:
    #         f = codecs.open(abs_path, "r", "utf-8")
    #         real_source = f.read()
    #         f.close()
    #         # line endings could be \r\n, but sublime text has only \n after
    #         # opening a file, so we have to calculate the offset betweet the
    #         # returned position and the real position by counting all \r before min
    #         # should be moved to a utility function
    #         offset = 0
    #         for i in range(0,min):
                
    #             if real_source[i] == u"\r":
    #                 offset += 1
    #         log("offset: " + str(offset))

    #         min -= offset

    #     if (abs_path == temp_file):
    #         # file is active view
    #         abs_path = view.file_name()
    #         target_view = view


    #         log("line ending: " + str(view.settings().get("line_ending")))

    #         target_view.sel().clear()
    #         target_view.sel().add(sublime.Region(min))

    #         target_view.show(sublime.Region(min))
    #     else:
    #         global find_decl_pos, find_decl_file
    #         find_decl_file = abs_path
    #         find_decl_pos = min
    #         # open file and listen => HaxeFindDeclarationListener
    #         target_view = view.window().open_file(abs_path)


