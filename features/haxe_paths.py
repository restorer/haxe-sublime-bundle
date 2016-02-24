import sublime
import os
import json

print("hello")

def haxe_path( key = 'haxe' ):
	
	view = sublime.active_window().active_view()

	if view is not None :

		settings = view.settings()
		if settings.has( key + "_path"):
			return settings.get( key + "_path")

		folders = view.window().folders()

		for f in folders:
			haxe = haxe_from_npm( os.path.join(f, "package.json"), key )
			if haxe is not None:
				return haxe

	return "haxe"

def haxelib_path():
	return haxe_path( 'haxelib' )

def haxe_from_npm( package_json , cmd = 'haxe' ):
	if( os.path.exists( package_json ) ):
		with open( package_json ) as f:
			pdata = json.load( f )
			if pdata['dependencies']['haxe'] is not None:
				bin_path = os.path.join( os.path.dirname(package_json), "node_modules", ".bin", cmd )
				if os.path.exists( bin_path ):
					return bin_path;
				else:
					print('Please run `npm install` to install Haxe')

	return None
