class ExtractBuildPathException (Exception):
	def __init__(self, build):
		Exception.__init__(self, "Cannot ExtractBuildPath from build " + str(build))

class GetRelativePathException (Exception):
	def __init__(self, build, file):
		Exception.__init__(self, "Cannot get the relative path of " + str(file) + " for build " + str(build))


class CreateTempFileOrFolderException (Exception):
	def __init__(self, build, file_or_folder):
		Exception.__init__(self, "Cannot create temp file or folder (" + str(file_or_folder) + ") from build (" + str(build) + ")")
