
import re


from haxe.tools.decorator import lazyprop
from haxe.log import log
import haxe.hxtools as hxsrctools
import haxe.config as hxconfig

def has_upper_first (s):
    return s[0].isupper()

def join_with_type(pre, type):
    if len(pre) > 0:
        res = pre + "." + type
    else:
        res = type
    return res

def pack_convert(pack):
    if len(pack) > 0:
        if pack[0] in ["flash8", "flash9"]:
            pack[0] = "flash"
    return pack


class HxType:
    def __init__(self, path):
        self.path = path
        self.parts = path.split(".")

    @lazyprop
    def is_enum_value (self):
        p = self.parts
        l = self.num_parts
        return l >= 3 and has_upper_first(p[l-2]) and has_upper_first(p[l-3])

    @lazyprop
    def num_parts(self):
        return len(self.parts)

    @lazyprop
    def enum_value_name (self):
        return self.parts[self.num_parts-1] if self.is_enum_value else None

    @lazyprop
    def type_name (self):
        p = self.parts
        l = self.num_parts
        return p[l-2] if self.is_enum_value else p[l-1]

    @lazyprop
    def full_pack_with_module_and_type (self):
        return join_with_type(self.full_pack_with_module, self.type_name)

    

    @lazyprop
    def full_pack_with_optional_module_and_type (self):
        return join_with_type(self.pack_with_optional_module_joined, self.type_name)

    @lazyprop
    def full_pack_with_optional_module_type_and_enum_value (self):
        return join_with_type(self.pack_with_optional_module_joined, self.type_name_with_optional_enum_value)
        

    @lazyprop
    def full_pack_with_module(self):
        return join_with_type(self.pack_joined, self.module_name)

    @lazyprop
    def full_pack_with_module_type_and_enum_value (self):
        return join_with_type(self.full_pack_with_module, self.type_name_with_optional_enum_value)

    @lazyprop
    def type_name_with_optional_enum_value (self):
        res = self.type_name
        if self.is_enum_value:
            res = res + "." + self.enum_value_name
        return res

    @lazyprop
    def module_name(self):
        for p in self.parts:
            if has_upper_first(p):
                return p
        return None

    @lazyprop
    def toplevel_pack(self):
        res = None
        if len(self.pack) > 0:
            res = self.pack[0]
        return res

    @lazyprop
    def pack_joined(self):
        return ".".join(self.pack)

    @lazyprop
    def pack(self):
        pack = []
        for p in self.parts:
            if not has_upper_first(p):
                pack.append(p)
            else:
                break
        return pack_convert(pack)

    @lazyprop
    def pack_with_optional_module_joined(self):
        return ".".join(self.pack_with_optional_module)

    @lazyprop
    def pack_with_optional_module(self):
        p = list(self.pack)
        if (not self.type_has_same_name_as_module):
            p.append(self.module_name)
        return p

    @lazyprop
    def type_has_same_name_as_module (self):
        return self.type_name == self.module_name

    @lazyprop
    def type_hint (self):
        return "enum value" if self.is_enum_value else "class"

    @lazyprop
    def can_be_ignored (self):
        return self.path in hxconfig.ignored_types





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

def get_packages (ctx, build_packs):
    packs = []
    std_packages = []
    build_target = get_build_target(ctx)
    for p in ctx.project.std_packages :
        if ctx.build.is_package_available(p):
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

def get_packs_and_types (ctx):
    
    build_classes , build_packs = ctx.build.get_types()

    cl = get_local_types(ctx)

    imported = get_imports(ctx)

    build_classes = filter_duplicate_types(build_classes, cl)


    cl.extend( ctx.build.std_classes )
    
    cl.extend( build_classes )
    
    cl.sort();

    packs = get_packages(ctx, build_packs)

    return packs, cl, imported




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



def get_snippet_insert(type, import_list):
    r = type_is_imported_as(import_list, type)
    if not r:
        r = type.full_pack_with_optional_module_type_and_enum_value
    return r

def get_snippet_display(type):
    return type.type_name_with_optional_enum_value + "\t" + type.type_hint

def get_snippet(type, import_list):
    return (get_snippet_display(type), get_snippet_insert(type, import_list))

def get_type_comps (ctx, cl, imported):
    build_target = get_build_target(ctx)
    comps = []
    packs = []
    inserted = dict()
    for c in cl :
        ht = HxType(c)
        if ht.can_be_ignored:
            continue
        
        full = ht.full_pack_with_optional_module_type_and_enum_value
        if not full in inserted and ctx.build.is_package_available(ht.toplevel_pack):
            
            inserted[full] = True
            cm = get_snippet(ht, imported)

            if len(ht.pack) > 0:
                packs.append(ht.pack_joined)

            comps.append( cm )
    return comps,packs


def get_toplevel_completion( ctx  ) :
    comps = []
    comps.extend(get_toplevel_keywords(ctx))
    
    packs, cl, imported = get_packs_and_types(ctx)
    
    if not ctx.is_new:
        comps.extend(get_local_vars_and_functions(ctx))
        
    comps1, packs1 = get_type_comps(ctx, cl, imported)

    comps.extend(comps1)
    
    packs.extend(packs1)
    
    for p in packs :
        cm = (p + "\tpackage",p)
        if cm not in comps :
            comps.append(cm)
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


