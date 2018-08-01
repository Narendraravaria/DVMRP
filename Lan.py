# Lan class

class Lan():
	def __init__ (self, id = None, dist = 10, nextHop = None, childBitMap = 0, leafBitMap = 0, isAnyRouterUsingMe = dict(), NMRFlag = 0, NMRDict = dict(), NMRRout = dict() ):
		self.id = id;
		self.dist = dist;
		self.nextHop = nextHop;
		self.childBitMap = childBitMap;
		self.leafBitMap = leafBitMap;
		self.pos = 0;
		self.isAnyRouterUsingMe = isAnyRouterUsingMe;
		self.NMRFlag = NMRFlag;
		self.NMRDict = NMRDict;
		self.NMRRout = NMRRout;

	def display(self):
		print "id:",self.id," dist: ",self.dist," nextHop: ",self.nextHop;




