## Netwerken en Systeembeveiliging Lab 5 - Distributed Sensor Network
## NAME: 			Jeroen Vranken & Mees Froberg
## STUDENT ID:			10658491   &   10559949
## Group: 11
##
## Represent a single node in the network
##

import sys
import struct
import time
import select

from socket import *
from random import randint
from gui import MainWindow
from sensor import *
from neighbour import *
from wave import *

class Node(object):
	def __init__(self, mcast_addr, sensor_pos, sensor_range, sensor_val, win):
		self.pos = sensor_pos
		self.range = sensor_range
		self.val = sensor_val
		self.readable = None
		self.writeable = None
		self.exceptional = None
		self.window = win
		self.neighbours = {}
		self.sequence = 0
		self.wave = []
		
		# -- Create the multicast listener socket. --
		self.mcast = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)
		# Sets the socket address as reusable so you can run multiple instances
		# of the program on the same machine at the same time.

		self.mcast.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
		# Subscribe the socket to multicast messages from the given address.
		mreq = struct.pack('4sl', inet_aton(mcast_addr[0]), INADDR_ANY)
		self.mcast.setsockopt(IPPROTO_IP, IP_ADD_MEMBERSHIP, mreq)
		if sys.platform == 'win32': # windows special case
			self.mcast.bind( ('localhost', mcast_addr[1]) )
		else: # should work for everything else
			self.mcast.bind(mcast_addr)

		# -- Create the peer-to-peer socket. --
		self.peer = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)
		# Set the socket multicast TTL so it can send multicast messages.
		self.peer.setsockopt(IPPROTO_IP, IP_MULTICAST_TTL, 5)
		# Bind the socket to a random port.
		if sys.platform == 'win32': # windows special case
			self.peer.bind( ('localhost', INADDR_ANY) )
		else: # should work for everything else
			self.peer.bind( ('', INADDR_ANY) )
		
		self.writeln( 'my address is %s:%s' % self.peer.getsockname() )
		self.writeln( 'my position is (%s, %s)' % self.pos )
		self.writeln( 'my sensor value is %s' % self.val )
	
	# Writes a line to the GUI		
	def writeln(self, string):
		self.window.writeln(string)
		
	# Resets the neighbour list, sends a multicast ping message
	def sendPing(self):
		self.neighbours = {}
		message = message_encode(MSG_PING, 0, self.pos, self.pos)
		for c in self.writeable:
			c.sendto(message, self.mcast.getsockname())

	# Sends a pong message to the given address
	def sendPong(self, addr):
		message = message_encode(MSG_PONG, 0, self.pos, self.pos)
		self.peer.sendto(message, addr)
	
	# Runs the select statement to update the readable and writeable sockets
	def updateSelect(self):
		self.readable, self.writeable, self.exceptional = select.select([self.mcast, self.peer], [self.peer], [], 0)

	# Adds a new neigbour to the nodes neighbour dictionary
	def updateNeighbours(self, initiator, addr):
		self.neighbours[initiator] = addr

	# Write all the neighbours to the GUI
	def listNeighbours(self):
		self.writeln("All neighbours:")
		for n in self.neighbours:
			self.writeln("Pos: " + str(n) + " Address: " + str(self.neighbours[n][0]) + ":" + str(self.neighbours[n][1]) )

	# Initate an echo wave, sets the corresponding operation field
	def initiateEcho(self, operation):
		self.writeln("Initiating wave: " + str(self.sequence) + " with operation: " + str(operation))
		wave = Wave(self.pos, self.pos, None, self.sequence, operation, self.val, 0)
		self.wave.append(wave)

		# Loops over all neighbours, sends each neighbour an echo message
		for n in self.neighbours.values():
			message = message_encode(MSG_ECHO, self.sequence, self.pos, self.pos, wave.operation, wave.capability, wave.payload)
			self.peer.sendto(message, n)

		# Increases the sequence number
		self.sequence += 1


	# Creates a wave with the received message, checks if it is a new wave, sends corresponding echo, or echo replies
	def createWave(self, message):
		# Check if the node already received an identical echo message
		newWave = True
		wave = Wave(message['initiator'], message['neighbour'], message['addr'], message['sequence'], message['operation'], message['capability'], message['payload'])
		
		for w in self.wave:
			if w.initiator == wave.initiator and w.sequence == wave.sequence:
				newWave = False
		
		if newWave:
			# If only one neighbour node, this node must be the father, send echo reply
			if len(self.neighbours) == 1:
				self.sendEchoReply(wave)
			else:
				self.wave.append(wave)
				self.sendEcho(wave)
		# Node already received this message
		else:
			wave.setPayload(0)
			self.sendEchoReply(wave)

	# Sends an echo to all neighbours, except the father
	def sendEcho(self, wave):
		for n in self.neighbours.values():
			if n != wave.fatherAddr:
				message = message_encode(MSG_ECHO, wave.sequence, wave.initiator, self.pos, wave.operation, wave.capability, wave.payload)
				self.peer.sendto(message, n)


	# Sends an echo reply to the father node
	def sendEchoReply(self, wave):

		if wave.operation == OP_SIZE:
			wave.incrementPayload()
		
		elif wave.operation == OP_SUM:
			wave.setPayload(wave.payload + self.val)
		
		elif wave.operation == OP_SAME:
			if wave.capability == self.val:
				wave.incrementPayload()
		
		elif wave.operation == OP_MIN:
			if wave.capability > self.val:
				wave.setCapability(self.val)

		elif wave.operation == OP_MAX:
			if wave.capability < self.val:
				wave.setCapability(self.val)

		message = message_encode(MSG_ECHO_REPLY, wave.sequence, wave.initiator, self.pos, wave.operation, wave.capability, wave.payload)
		self.peer.sendto(message, wave.fatherAddr)

	# Returns true if a node received replies from all his neighbours except his father
	def receivedAllReplies(self, wave):
		result = True
		for n in self.neighbours:
			if (n != wave.fatherPos) and (n not in wave.repliesFrom):
				result = False
		return result
			
	def setPos(self, pos):
		self.pos = pos

	def setVal(self, value):
		self.val = value


