from haxe.log import log
import haxe.hxtools as hxsrctools
import haxe.config as hxconfig
import re

def is_package_available (target, pack):
    cls = hxconfig
    res = True
    
    if target != None and pack in cls.target_packages:
        if target in cls.target_std_packages:
            if pack not in cls.target_std_packages[target]:
                res = False;

    return res


def get_toplevel_keywords (ctx):

    res = None
    
    if ctx.is_new:
        res = []
    else:
        res = [("trace\ttoplevel","trace"),("this\ttoplevel","this"),("super\ttoplevel","super")]
    
    return res

def get_build_target(ctx):
    return "neko" if ctx.options.macro_completion else ctx.build.target


def get_local_vars_and_functions (ctx):
    comps = []
    for v in hxsrctools.variables.findall(ctx.src) :
        comps.append(( v + "\tvar" , v ))

    for f in hxsrctools.named_functions.findall(ctx.src) :
        if f not in ["new"] :
            comps.append(( f + "\tfunction" , f ))
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

def get_packages (ctx, build_packs):
    packs = []
    std_packages = []
    build_target = get_build_target(ctx)
    for p in ctx.project.std_packages :
        if is_package_available(build_target, p):
            if p == "flash9" or p == "flash8" :
                p = "flash"
            std_packages.append(p)

    packs.extend( std_packages )
    packs.extend( build_packs ) 

    return packs


def get_imports (ctx):
    imports = hxsrctools.import_line.findall( ctx.src )
    imported = []
    for i in imports :
        imp = i[1]
        imported.append(imp)

    return imported

def filter_duplicate_types (types_to_filter, types):
    def filter_type (x):
        for c in types:
            if x == c:
                return False
        return True

    return filter(filter_type, types_to_filter)

def get_local_types (ctx):
    src = hxsrctools.comments.sub("",ctx.src)
    cl = []
    local_types = hxsrctools.type_decl.findall( src )
    for t in local_types :
        if t[1] not in cl:
            cl.append( t[1] )
    return cl

def get_toplevel_completion( ctx  ) :
    
    project = ctx.project
    build = ctx.build
    

    
    build_target = get_build_target(ctx)

    comps = get_toplevel_keywords(ctx)
        

    #src = hxsrctools.comments.sub("",src)

    cl = get_local_types(ctx)


    
    imported = get_imports(ctx)
    

    build_classes , build_packs = build.get_types()

    log("number of build classes: " + str(len(build_classes)))

    build_classes = filter_duplicate_types(build_classes, cl)

    cl.extend( project.std_classes )
    
    cl.extend( build_classes )
    
    cl.sort();

    log("target: " + str(build_target))

    packs = get_packages(ctx, build_packs)
    
    
    if not ctx.is_new:
        comps.extend(get_local_vars_and_functions(ctx))
        

    for c in cl :
        spl = c.split(".")
        if spl[0] == "flash9" or spl[0] == "flash8" :
            spl[0] = "flash"

        if c in hxconfig.ignored_types:
            continue

        top = spl[0]
        
        clname = spl.pop()
        enum_name = None;

        if len(spl) >= 2:
            last1 = spl[len(spl)-2]
            last2 = spl[len(spl)-1]

            if last1[0].isupper():
                enum_name = last2
                spl.pop()
                if enum_name == last1:
                    spl.pop();
                     
        pack = ".".join(spl)

        display = clname

        if enum_name is not None:
            spl.append(enum_name) 
            display = enum_name + "." + display

        if pack != "" :
            display += "\t" + pack
        else :
            display += "\tclass"
        
        
        
        spl.append(clname)
        
        is_imported = (pack in imported or c in imported 
                 or (enum_name != None and (pack + "." + enum_name) in imported))

        if is_imported:
           
            cm = ( display , clname )
            # at this point we could search for enum constructors and
            # add them to toplevel completion
        
        else :
            #add an option for full packages in completion, something like this:
            #cm = ( ".".join(spl) , ".".join(spl) )
            
            cm = ( display , ".".join(spl) )

        if cm not in comps and is_package_available(build_target, top):
            # add packages to completion
            
            z = [x for x in spl if len(x) > 0 and x[0].lower() == x[0]]
            if (len(z) > 0):
                p = ".".join(z)
                packs.append(p) 

            comps.append( cm )
        
    
    for p in packs :
        cm = (p + "\tpackage",p)
        if cm not in comps :
            comps.append(cm)

    #log("comps:" + str(comps))
    return comps

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
        comps = all_comps

    log("number of top level completions (all: " + str(len(all_comps)) + ", filtered: " + str(len(comps)) + ")")
    return comps