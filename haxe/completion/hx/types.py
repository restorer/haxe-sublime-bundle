import sublime
import re

import time

from haxe.plugin import is_st3


from haxe.tools.decorator import lazyprop
from haxe.tools import viewtools, stringtools
from haxe.log import log
from haxe.completion.hx import constants as hcc
from haxe import settings

control_struct = re.compile( "\s+(if|switch|for|while)\s*\($" );



def count_commas_and_complete_offset (src, prev_comma, complete_offset):
    commas = 0;
    closed_pars = 0
    closed_braces = 0
    closed_brackets = 0

    for i in range( prev_comma , 0 , -1 ) :
        c = src[i]
        if c == ")" :
            closed_pars += 1
        elif c == "(" :
            if closed_pars < 1 :
                complete_offset = i+1
                break
            else :
                closed_pars -= 1
        elif c == "," :
            if closed_pars == 0 and closed_braces == 0 and closed_brackets == 0 :
                commas += 1
        elif c == "{" :
            #commas = 0
            closed_braces -= 1

        elif c == "}" :
            closed_braces += 1
        elif c == "[" :
            #commas = 0
            closed_brackets -= 1
        elif c == "]" :
            closed_brackets += 1

    return (commas, complete_offset)


def get_completion_info (view, offset, src):
    prev = src[offset-1]
    commas = 0
    
    complete_offset = offset
    is_new = False
    prev_symbol_is_comma = False
    if (prev == " " and (offset-4 >= 0) and src[offset-4:offset-1] == "new"):
        is_new = True
    elif prev not in "(.;" :
        fragment = view.substr(sublime.Region(0,offset))
        prev_dot = fragment.rfind(".")
        prev_par = fragment.rfind("(")
        prev_comma = fragment.rfind(",")
        prev_colon = fragment.rfind(":")
        prev_brace = fragment.rfind("{")
        prev_semi = fragment.rfind(";")
        
        
        prev_symbol = max(prev_dot,prev_par,prev_comma,prev_brace,prev_colon, prev_semi)
        
        if prev_symbol == prev_comma:
            commas, complete_offset = count_commas_and_complete_offset(src, prev_comma, complete_offset)
            #print("closedBrackets : " + str(closedBrackets))
            prev_symbol_is_comma = True
        else :
            complete_offset = max( prev_dot + 1, prev_par + 1 , prev_colon + 1, prev_brace + 1, prev_semi + 1 )
            
    log("COMPLETE_CHAR:" + src[complete_offset-1])
    return (commas, complete_offset, prev_symbol_is_comma, is_new)



def get_completion_id ():
    # make the current time the id for this completion
    return time.time()

class CompletionOptions:
    def __init__(self, trigger, context = hcc.COMPILER_CONTEXT_REGULAR, types = hcc.COMPLETION_TYPE_REGULAR, toplevel = hcc.COMPLETION_TYPE_TOPLEVEL):
        self._types = CompletionTypes(types)
        self._toplevel = TopLevelOptions(toplevel)
        self._context = context
        self._trigger = trigger

    def copy_as_manual(self):
        return CompletionOptions(hcc.COMPLETION_TRIGGER_MANUAL, self._context, self.types.val, self._toplevel.val)

    def copy_as_async(self):
        return CompletionOptions(hcc.COMPLETION_TRIGGER_ASYNC, self._context, self.types.val, self._toplevel.val)

    @property
    def types(self):
        return self._types


    @lazyprop
    def async_trigger(self):
        return self._trigger == hcc.COMPLETION_TRIGGER_ASYNC

    @lazyprop
    def manual_completion(self):
        return self._trigger == hcc.COMPLETION_TRIGGER_MANUAL

    @lazyprop
    def macro_completion(self):
        return self._context == hcc.COMPILER_CONTEXT_MACRO

    @lazyprop
    def regular_completion(self):
        return self._context == hcc.COMPILER_CONTEXT_REGULAR

    def eq (self, other):
        return self._trigger == other._trigger and self._types.eq(other._types) and self._toplevel.eq(other._toplevel) and self._context == other._context


class CompletionTypes:

    def __init__(self, val = hcc.COMPLETION_TYPE_REGULAR):
        self._opt = val

    @property
    def val (self):
        return self._opt

    def add (self, val):
        self._opt |= val

    def add_hint (self):
        self._opt = self._opt | hcc.COMPLETION_TYPE_HINT

    def has_regular (self):
        return (self._opt & hcc.COMPLETION_TYPE_REGULAR) > 0

    def has_hint (self):
        return (self._opt & hcc.COMPLETION_TYPE_HINT) > 0
    
    def has_toplevel (self):
        return (self._opt & hcc.COMPLETION_TYPE_TOPLEVEL) > 0

    def has_toplevel_forced (self):
        return (self._opt & hcc.COMPLETION_TYPE_TOPLEVEL_FORCED) > 0

    def eq (self, other):
        return self._opt == other._opt

class TopLevelOptions:

    def __init__(self, val = 0):
        self._opt = val

    @property
    def val (self):
        return self._opt

    def set (self, val):
        self._opt |= val

    def has_types (self):
        return (self._opt & hcc.TOPLEVEL_OPTION_TYPES) > 0

    def has_locals (self):
        return (self._opt & hcc.TOPLEVEL_OPTION_LOCALS) > 0
    
    def has_keywords (self):
        return (self._opt & hcc.TOPLEVEL_OPTION_KEYWORDS) > 0

    def eq (self, other):
        return self._opt == other._opt

class CompletionSettings:
    def __init__(self, settings):
        self.settings = settings

    @lazyprop
    def smarts_hints_only_next(self):
        return self.settings.smarts_hints_only_next()

    @lazyprop
    def no_fuzzy_completion(self):
        return self.settings.no_fuzzy_completion()

    @lazyprop
    def top_level_completions_only_on_demand(self):
        return self.settings.top_level_completions_on_demand()

    @lazyprop
    def is_async_completion(self):
        return self.settings.is_async_completion()

    @lazyprop
    def show_only_async_completions(self):
        return self.settings.show_only_async_completions()

    @lazyprop
    def get_completion_delays(self):
        return self.settings.get_completion_delays()

    def show_completion_times(self, view):
        return self.settings.show_completion_times(view)

#
#class CompletionResult:
#    def __init__(self, toplevel, comps, hints, options, errors):
#        self.toplevel = toplevel
#        self.comps = comps
#        self.hints = hints
#        self.errors = errors
#        self.options = options
#
#    def to_sublime_completions (self):
#        res = []
#
#        if self.options.types.hasHint():     res.extend(hints_to_sublime_completions(self.hints))
#        if self.options.types.hasToplevel(): res.extend(self.toplevel)
#        if self.options.types.hasRegular():  res.extend(self.comps)
#
#        return res


class CompletionContext:
    def __init__(self, view, project, offset, options, settings, prefix):
        self.view = view

        self.prefix = prefix

        # position in src where auto completion was triggered
        self.offset = offset
    
        # current project
        self.project = project
        
        # context independent completion options
        self.options = options

        # user settings
        self.settings = settings

        self.view_id = view.id()

        self.id = get_completion_id()

        self.view_pos = viewtools.get_first_cursor_pos(view)
   

    @lazyprop
    def complete_offset_in_bytes(self):
        s = self.src_until_complete_offset
        if is_st3:
            s_bytes = s.encode()
        else:
            s_bytes = s.encode("utf-8")
        
        return len(s_bytes)

    @lazyprop
    def orig_file(self):
        return self.view.file_name()

    # build which is used for current compiler completion
    @lazyprop
    def build(self):
        if not self.project.has_build():
            self.project.extract_build_args()
        return self.project.get_build( self.view ).copy()

    # indicates if completion starts after the first ( after a control struct like while, if, for etc.
    @lazyprop
    def complete_char_is_after_control_struct(self):
        return self.in_control_struct and self.complete_char == "("

    @lazyprop
    def in_control_struct(self):
        return control_struct.search( self.src_until_complete_offset ) is not None

    @lazyprop
    def src_until_complete_offset(self):
        return self.src[0:self.complete_offset]

    @lazyprop 
    def line_after_offset(self):
        line_end = self.src.find("\n", self.offset)
        return self.src[self.offset:line_end]

    # src of current file
    @lazyprop
    def src (self):
        return viewtools.get_content(self.view)

    @lazyprop
    def complete_char (self):
        return self.src[self.complete_offset-1]

    @lazyprop
    def src_from_complete_to_offset(self):
        return self.src[self.complete_offset:self.offset]

    @lazyprop
    def src_from_complete_to_prefix_end(self):
        rest = self.src[self.complete_offset+1:self.offset+1 + len(self.prefix)]
        log("REEEEEEEEEEST:'" + rest + "'")
        return rest
                
    @lazyprop
    def offset_char (self):
        return self.src[self.offset]

    @lazyprop
    def _completion_info(self):
        log("CALLED ONCE")
        return get_completion_info(self.view, self.offset, self.src)

    @lazyprop
    def commas(self):
        return self._completion_info[0]

    @lazyprop
    def prev_symbol_is_comma(self):
        return self._completion_info[2]

    # position in source where compiler completion gets triggered
    @lazyprop
    def complete_offset(self):
        return self._completion_info[1]

    @lazyprop
    def is_new(self):
        return self._completion_info[3]

    @lazyprop
    def src_until_offset (self):
        return self.src[0:self.offset-1]

    @lazyprop
    def temp_completion_src(self):
        return self.src[:self.complete_offset] + "|" + self.src[self.complete_offset:]


    @lazyprop
    def prefix_is_whitespace(self):
        return stringtools.is_whitespace_or_empty(self.prefix)

    def eq (self, other):

        def prefix_check():
            prefix_same = True
            if self.options.types.has_hint():
                prefix_same = self.prefix == other.prefix or (self.prefix_is_whitespace and other.prefix_is_whitespace)

            log("same PREFIX:" + str(prefix_same))
            log("PREFIXES:" + self.prefix + " - " + other.prefix)
            return prefix_same

        return (
            self != None and other != None
        and self.orig_file == other.orig_file
        and self.offset == other.offset
        and self.commas == other.commas
        and self.src_until_offset == other.src_until_offset
        and self.options.eq(other.options)
        and self.complete_char == other.complete_char
        and self.line_after_offset == other.line_after_offset
        and prefix_check())

class CompletionInfo:
    def __init__(self, commas, complete_offset, toplevel_complete, is_new):
        self.commas = commas
        self.complete_offset = complete_offset
        self.toplevel_complete = toplevel_complete
        self.is_new = is_new



class CompletionResult:
    @staticmethod
    def empty_result (ctx, retrieve_toplevel_comps = None):
        return CompletionResult("", [], "", [], ctx, retrieve_toplevel_comps)


    def __init__(self, ret, comps, status, hints, ctx, retrieve_toplevel_comps = None):
        self.ret = ret
        self.comps = comps
        self.status = status
        self.hints = hints
        self.ctx = ctx
        if retrieve_toplevel_comps == None:
            retrieve_toplevel_comps = lambda:[]
        self.retrieve_toplevel_comps = retrieve_toplevel_comps

        

    @lazyprop
    def _toplevel_comps(self):
        return self.retrieve_toplevel_comps()


    def has_hints (self):
        return len(self.hints) > 0

    def has_compiler_results (self):
        return len(self.comps) > 0

    def has_results (self):
        return len(self.comps) > 0 or len(self.hints) > 0 or (self.requires_toplevel_comps() and len(self._toplevel_comps) > 0)

    def show_top_level_snippets (self):
        return self.requires_toplevel_comps() and not self.ctx.is_new

    

    def requires_toplevel_comps(self):
        prefix_is_whitespace = stringtools.is_whitespace_or_empty(self.ctx.prefix)
        log("prefix_is_whitespace:" + str(prefix_is_whitespace))
        log("has_hints:" + str(self.has_hints()))
        log("has_hint:" + str(self.ctx.options.types.has_hint()))
        log("has_compiler_results:" + str(self.has_compiler_results()))
        return not ((prefix_is_whitespace and self.has_hints() and self.ctx.options.types.has_hint()) or self.has_compiler_results())

    def all_comps (self):
        res = []
        if self.requires_toplevel_comps():
            log("yes required toplevel comps")
            res.extend(list(self._toplevel_comps))
        res.extend(self.comps)
        res.sort();
        return res


class CompletionBuild:
    def __init__(self, ctx, temp_path, temp_file):
        self.build = ctx.build.copy()
        # add the temp_path to the classpath of the build
        self.build.add_classpath(temp_path)
        # the completion context
        self.ctx = ctx
        # stores the temporary classpath which contains the temp_file
        self.temp_path = temp_path
        # stores the temporary file path which is used for completion
        self.temp_file = temp_file

        self.cache = ctx.project.completion_context.current

    @lazyprop
    def display(self):
        pos = ("0" if not settings.use_offset_completion() else  str(self.ctx.complete_offset_in_bytes))
        return self.temp_file + "@" + pos