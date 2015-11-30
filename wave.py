
class Wave(object):
	def __init__(self, initiator, father, addr, sequence):
		self.initiator = initiator
		self.fatherPos = father
		self.fatherAddr = addr
		self.sequence = sequence
		self.repliesFrom = []

	def addReply(self, neighbour):
		self.repliesFrom.append(neighbour)




