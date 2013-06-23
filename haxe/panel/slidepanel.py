import sublime

from haxe.tools import viewtools

from haxe.panel.tools import valid_message, haxe_file_regex, timestamp_msg

class SlidePanel ():
	
	def __init__ (self, win):
		self.win = win
		self.output_view = None

	def clear(self) :
		self.output_view = self.win.get_output_panel("haxe")

	def write( self , text , scope = None, show_timestamp = True ) :
		
		win = self.win

		if self.output_view is None :
			self.output_view = win.get_output_panel("haxe")

		self.output_view.settings().set("result_file_regex", haxe_file_regex())
		# force result buffer
		win.get_output_panel("haxe")
		
		panel = self.output_view
		
		if show_timestamp:	
			text = timestamp_msg(text);
		
		win.run_command("show_panel",{"panel":"output.haxe"})
		
		def do_edit(v, edit):
			region = sublime.Region(v.size(),v.size() + len(text))
			v.insert(edit, v.size(), text)
			v.end_edit( edit )
			
			if scope is not None :
				icon = "dot"
				key = "haxe-" + scope
				regions = v.get_regions( key );
				regions.append(region)
				v.add_regions( key , regions , scope , icon )

			# set seletion to the begin of the document, allows navigating
			# through errors from the start
			v.sel().clear()
			v.sel().add(sublime.Region(0))

			#region = sublime.Region(v.size()+1000, v.size()+1000)
			#sublime.set_timeout(lambda:v.show(region), 800)
		
		viewtools.async_edit(panel, do_edit)

		return panel

	def writeln (self, msg, scope = None, show_timestamp = True):
		if valid_message(msg):
			self.write(msg + "\n", scope, show_timestamp)

	def status (self, title, msg):
		if valid_message(msg):
			self.writeln(title + ": " + msg)