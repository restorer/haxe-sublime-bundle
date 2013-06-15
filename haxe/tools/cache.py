import time

class Cache:
	def __init__ (self, cache_time = -1 ):
		self.data = {}
		self.cache_time = cache_time
		self.time_driven = cache_time != -1

	def insert (self, id, value):
		self.data[id] = (time.time(), value)

	def exists (self, id):
		return self.get_or_default(id, None) != None
	
	def get_or_insert (self, id, creator):
		res = None
		if id in self.data:
			res = self._get_val(id)
		else:
			res = creator()
			self.insert(id, res)
		return res

	def _get_val (self, id):
		return self.data[id][1]

	def _cache_invalid (self, id):
		return not self._cache_valid(id)

	def _cache_valid (self, id):
		now = time.time()
		return now - self.data[id][0] <= self.cache_time

	def get_or_default (self, id, default = None):
		res = default
		if id in self.data:
			if self.time_driven and self._cache_invalid(id):
				del self.data[id]
			else:
				res = self._get_val(id)
		return res

	def get_and_delete (self, id, default=None):
		val = default
		if id in self.data:
			if not self.time_driven or self._cache_valid(id):
				val = self._get_val(id)
			del self.data[id]
		return val

	def delete (self, id):
		if (id in self.data):
			del self.data[id]