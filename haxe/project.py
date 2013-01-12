
import sublime
import os



class Project():

	@staticmethod
	def folders ():
		return sublime.active_window().folders()

	@staticmethod
	def main_folder ():
		for f in Project.folders():
			if os.path.exists(f +  "/.haxeproject"):
				return f
		return None



	@staticmethod 
	def create_main_folder ():
		folders1 = Project.folders()

		suggested_folder = folders1[0] if folders1 else os.path.expanduser("~")
		w = sublime.active_window()

		w.show_input_panel("Enter project root:", suggested_folder, Project.main_folder_selected, None, None)


	@staticmethod
	def main_folder_selected (path):
		dir = path + "/.haxeproject"
		os.makedirs(dir)
		

	

		


 
#print Project.create_main_folder()
		