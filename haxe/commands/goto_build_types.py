from haxe.commands import HaxeGotoBaseCommand

class HaxeGotoBuildTypesCommand( HaxeGotoBaseCommand ):

    def get_entries (self, types):
        return [[k, types[k].file] for k in types]
        
    def get_data (self, types):
        return [(k,types[k]) for k in types]

    def get_file(self, data_entry):
        return data_entry.file

    def get_src_pos(self, data_entry):
        return data_entry.src_pos
