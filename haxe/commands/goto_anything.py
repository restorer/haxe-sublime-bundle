
from haxe.commands import HaxeGotoBaseCommand
    

class HaxeGotoAnythingCommand( HaxeGotoBaseCommand ):

    def get_entries (self, types):
        fields = [[p.to_string() + " - " + p.kind, p.type.file] for k in types for p in types[k].all_fields_list]
        types = [[k, types[k].file] for k in types]
        fields.extend(types)
        return fields
        
    def get_data (self, types):
        fields = [(k + "." + p.name,p) for k in types for p in types[k].all_fields_list]
        types = [(k,types[k]) for k in types]
        fields.extend(types)
        return fields

    def get_file(self, data_entry):
        return data_entry.file

    def get_src_pos(self, data_entry):
        return data_entry.src_pos
