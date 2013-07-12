import re
import sys
from haxe.plugin import is_st3, is_st2

def startswith_any (s, list_str):
	for s1 in list_str:
		if s.startswith(s1):
			return True
	return False

def reverse (s):
	return s[::-1]



_whitespace = re.compile("^\s*$")

def is_whitespace_or_empty(s):
	return re.match(_whitespace, s) is not None


def unicode_to_str(s, encoding, add = ""):
	if is_st3:
		return s.decode(encoding, add)
	else:
		return s.encode(encoding, add)

def str_to_unicode_to_str (s, encoding1, encoding2):
	return unicode_to_str(str_to_unicode(s, encoding1), encoding2)

def str_to_unicode(s, encoding, add = ""):
	if is_st3:
		return s.encode(encoding, add)
	else:
		return s.decode(encoding, add)


def to_unicode (s):
	if s is None:
		return s
	if is_st3 and isinstance(s, bytes):
		res = s
	elif is_st2 and isinstance(s, unicode):
		res = s
	elif isinstance(s, str):
		try:
			res = str_to_unicode(s, "utf-8", "ignore")
		except:
			try:
				res = str_to_unicode(s,"ascii")
			except:
				try:
					res = str_to_unicode(s,"iso-8859-1")
				except:
					try:
						res = str_to_unicode(s,"ascii")
					except:
						raise DecodeException("cannot decode str")
	else:
		s = s
	return res

class DecodeException(BaseException):
	def __init__(self, m):
		self.message = m
	def __str__(self):
		return self.message

class EncodeException(BaseException):
	def __init__(self, m):
		self.message = m
	def __str__(self):
		return self.message

def st3_encode_utf8 (s):
	if is_st3:
		return encode_utf8(s)
	else:
		return s

def st2_encode_utf8 (s):
	if is_st3:
		return s
	else:
		return encode_utf8(s)


def st2_to_unicode(s):
	if is_st2:
		return to_unicode(s)
	else:
		return s

def encode_utf8 (s):
	if s is None:
		return s
	if is_st3 and isinstance(s, bytes):
		res = s.decode("utf-8", "ignore")
	else:
		if is_st2 and isinstance(s, unicode):
			#print("it's unicode")
			res = unicode_to_str(s, "utf-8", "ignore")
		elif isinstance(s, str):
			try:
				#print("try utf8 decode")
				res = s.decode("utf-8")
				#res = s
			except:
				try:
					#print("try ascii decode")
					res = str_to_unicode_to_str(s, "ascii", "utf-8")
				except:
					try:
						#print("try iso8859-1 decode")
						res = str_to_unicode_to_str(s, "iso-8859-1", "utf-8")
					except: 
						#print("cannot decode")
						raise EncodeException("cannot decode str")
		else:
			#print("it's not a str or unicode, it's" + str(type(s)))
			raise EncodeException("it's not a str or unicode, it's" + str(type(s)))
			res = s
	#print("result type: " + str(type(res)))
	return res

			