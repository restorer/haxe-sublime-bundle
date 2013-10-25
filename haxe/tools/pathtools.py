import os
import shutil

def remove_dir(path):
	if os.path.isdir(path):
		shutil.rmtree(path)

def join_norm(path1, path2):
	return os.path.normpath(os.path.join(path1, path2))

def is_abs_path(path):
	return os.path.normpath(path) == os.path.abspath(path)
