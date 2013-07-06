import re

from haxe.tools.decorator import lazyprop

from haxe.tools import hxsrctools

from haxe.log import log

import haxe.config as hxconfig

import time


TOP_LEVEL_KEYWORDS = [("trace\ttoplevel","trace"),("this\ttoplevel","this"),("super\ttoplevel","super")]

def get_toplevel_keywords (ctx):
    return [] if ctx.is_new else TOP_LEVEL_KEYWORDS
    

def get_build_target(ctx):
    return "neko" if ctx.options.macro_completion else ctx.build.target


def get_local_vars(ctx):
    comps = []
    for v in hxsrctools.variables.findall(ctx.src) :
        comps.append(( v + "\tvar" , v ))
    return comps

def get_local_functions(ctx):
    comps = []
    for f in hxsrctools.named_functions.findall(ctx.src) :
        if f not in ["new"] :
            comps.append(( f + "\tfunction" , f ))    
    return comps

def get_local_function_params(ctx):
    comps = []
    #TODO can we restrict this to local scope ?
    for params_text in hxsrctools.function_params.findall(ctx.src) :
        cleaned_params_text = re.sub(hxsrctools.param_default,"",params_text)
        params_list = cleaned_params_text.split(",")
        for param in params_list:
            a = param.strip();
            if a.startswith("?"):
                a = a[1:]
            
            idx = a.find(":") 
            if idx > -1:
                a = a[0:idx]

            idx = a.find("=")
            if idx > -1:
                a = a[0:idx]
                
            a = a.strip()
            cm = (a + "\tvar", a)
            if cm not in comps:
                comps.append( cm )
    return comps

def get_local_vars_and_functions (ctx):
    comps = []
    comps.extend(get_local_vars(ctx))
    comps.extend(get_local_functions(ctx))
    comps.extend(get_local_function_params(ctx))

    return comps

def get_imports (ctx):
    imports = hxsrctools.import_line.findall( ctx.src )
    imported = []
    for i in imports :
        imp = i[1]
        imported.append(imp)

    return imported

def get_usings (ctx):
    usings = hxsrctools.using_line.findall( ctx.src )
    used = []
    for i in usings :
        imp = i[1]
        used.append(imp)

    return used

def get_imports_and_usings (ctx):
    res = get_imports(ctx)
    
    res.extend(get_usings(ctx))

    return res


def haxe_type_as_completion (type):
    insert = type.full_pack_with_optional_module_type_and_enum_value
    display = type.type_name_with_optional_enum_value
    display += "\t" + type.get_type_hint
    return (display, insert)

def type_is_imported_as(import_list, type):
    res = False
    for i in import_list:
        res = None
        if type.full_pack_with_module == i or type.full_pack_with_module_and_type == i or type.full_pack_with_optional_module_and_type  == i:
            if type.is_enum_value: 
                res = type.enum_value_name
            else: 
                res = type.type_name_with_optional_enum_value
            
        elif type.full_pack_with_optional_module_type_and_enum_value  == i or type.full_pack_with_module_type_and_enum_value  == i:
            res = type.enum_value_name
        if res != None:
            break
    return res


def get_type_comps (ctx, bundle, imported):
    build_target = get_build_target(ctx)
    comps = []
    
    for t in bundle.all_types():
        if ctx.build.is_type_available(t):
            snippets = t.to_snippets(imported, ctx.orig_file)
            comps.extend(snippets)

    for p in bundle.packs():
        if ctx.build.is_pack_available(p):
            cm = (p + "\tpackage",p)
            comps.append(cm)

    return comps


def get_toplevel_completion( ctx  ) :
    start_time = time.time()
    comps = []
    
    if not ctx.is_new:
        comps.extend(get_toplevel_keywords(ctx))
        comps.extend(get_local_vars_and_functions(ctx))


    imported = get_imports_and_usings(ctx)

    run_time1 = time.time() - start_time

    build_bundle = ctx.build.get_types()

    run_time2 = time.time() - start_time

    std_bundle = ctx.build.std_bundle


    def filter_privates(t):
        return not t.is_private or t.file == ctx.orig_file

    merged_bundle = std_bundle.merge(build_bundle).filter(filter_privates)

    run_time3 = time.time() - start_time

    comps1 = get_type_comps(ctx, merged_bundle, imported)

    run_time4 = time.time() - start_time

    comps.extend(comps1)
    
    run_time = time.time() - start_time

    log("TOP LEVEL COMPLETION TIME1:" + str(run_time1))
    log("TOP LEVEL COMPLETION TIME2:" + str(run_time2))
    log("TOP LEVEL COMPLETION TIME3:" + str(run_time3))
    log("TOP LEVEL COMPLETION TIME4:" + str(run_time4))
    log("TOP LEVEL COMPLETION TIME END:" + str(run_time))

    return comps

def get_toplevel_completion_filtered(ctx):
    comps = get_toplevel_completion(ctx)
    return filter_top_level_completions(ctx.offset_char, comps)

def filter_top_level_completions (offset_char, all_comps):
        
    comps = []

    is_lower = offset_char in "abcdefghijklmnopqrstuvwxyz"
    is_upper = offset_char in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    is_digit = offset_char in "0123456789"
    is_special = offset_char in "$_#"
    
    if is_lower or is_upper or is_digit or is_special:
        offset_upper = offset_char.upper()
        offset_lower = offset_char.lower()

        for c in all_comps:

            id = c[1]

            if (offset_char in id
                or (is_upper and offset_lower in id)
                or (is_lower and offset_upper in id)):
                comps.append(c)
    else:
        comps = list(all_comps)

    log("number of top level completions (all: " + str(len(all_comps)) + ", filtered: " + str(len(comps)) + ")")
    return comps


