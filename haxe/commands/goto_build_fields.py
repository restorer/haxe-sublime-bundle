
from haxe.commands import HaxeGotoBaseCommand
    

class HaxeGotoBuildFieldsCommand( HaxeGotoBaseCommand ):

    def get_entries (self, types):
        return [[p.to_string() + " - " + p.kind, p.type.file] for k in types for p in types[k].all_fields_list]
        
    def get_data (self, types):
        return [(k + "." + p.name,p) for k in types for p in types[k].all_fields_list]

    def get_file(self, data_entry):
        return data_entry.type.file

    def get_src_pos(self, data_entry):
        return data_entry.src_pos
