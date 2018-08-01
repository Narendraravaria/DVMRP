class Node(object):
	"""docstring for Node"""
	def __init__(self, id_num, mode):
		self.id = id_num;
		self.type = mode;
		self.filename = mode+id_num;
		self.pos = 0;