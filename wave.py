## Netwerken en Systeembeveiliging Lab 5 - Distributed Sensor Network
## NAME: 			Jeroen Vranken & Mees Froberg
## STUDENT ID:			10658491   &   10559949
## Group: 11
##
## Represent a single wave from the perspective of one single node 
##


class Wave(object):
	def __init__(self, initiator, father, addr, sequence, operation, capability, payload):
		self.initiator = initiator
		self.fatherPos = father
		self.fatherAddr = addr
		self.sequence = sequence
		self.repliesFrom = []
		self.operation = operation
		self.payload = payload
		self.capability = capability

	def addReply(self, neighbour):
		self.repliesFrom.append(neighbour)

	def incrementPayload(self):
		self.payload += 1

	def setPayload(self, payload):
		self.payload = payload

	def setCapability(self, capability):
		self.capability = capability