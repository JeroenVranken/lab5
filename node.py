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
		if sys.platform.startswith('darwin'):
			print "Dit is een mac!"
			self.mcast.setsockopt(SOL_SOCKET, SO_REUSEPORT, 1)
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
			
	def writeln(self, string):
		self.window.writeln(string)
		
	def sendPing(self):
		self.neighbours = {}
		message = message_encode(MSG_PING, 0, self.pos, self.pos)
		for c in self.writeable:
			c.sendto(message, self.mcast.getsockname())
			# self.writeln("Send ping message")

	def sendPong(self, addr):
		message = message_encode(MSG_PONG, 0, self.pos, self.pos)
		self.peer.sendto(message, addr)
		# self.writeln("Send pong to: "+ str(addr))
	
	def updateSelect(self):
		self.readable, self.writeable, self.exceptional = select.select([self.mcast, self.peer], [self.peer], [], 0)

	def updateNeighbours(self, initiator, addr):
		# self.writeln("updateNeighbours " + str(initiator) + ": " + str(addr))
		# self.writeln("updatig neighbour:" + str(initiator) + " " + str(addr))
		self.neighbours[initiator] = addr

	def listNeighbours(self):
		print self.writeln(self.neighbours)

	def initiateEcho(self):
		wave = Wave(self.pos, self.pos, None, self.sequence)
		self.wave.append(wave)
		for n in self.neighbours.values():
			message = message_encode(MSG_ECHO, self.sequence, self.pos, self.pos)
			self.peer.sendto(message, n)

		self.sequence += 1

	def createWave(self, message):
		newWave = True
		wave = Wave(message['initiator'], message['neighbour'], message['addr'], message['sequence'])
		for w in self.wave:
			if w.initiator == wave.initiator and w.sequence == wave.sequence:
				newWave = False
		if newWave:
			if len(self.neighbours) == 1:
				self.sendEchoReply(wave)
			else:
				self.writeln("Creating new wave")
				self.wave.append(wave)
				self.sendEcho(wave)
		else:
			self.sendEchoReply(wave)

	def sendEcho(self, wave):
		# self.writeln("sendEcho")
		for n in self.neighbours.values():
			if n != wave.fatherAddr:
				self.writeln("sendEcho forreal: " + str(n))
				message = message_encode(MSG_ECHO, wave.sequence, wave.initiator, self.pos)
				# ip, port = self.neighbours[n]
				self.peer.sendto(message, n)
				self.writeln("self.neighbours[n] :" + str(n))


	def sendEchoReply(self, wave):
		self.writeln("sendEchoReply to " + str(wave.fatherPos))
		message = message_encode(MSG_ECHO_REPLY, wave.sequence, wave.initiator, self.pos)
		self.peer.sendto(message, wave.fatherAddr)


	def receivedAllReplies(self, wave):
		result = True
		for n in self.neighbours:
			if (n != wave.fatherPos) and (n not in wave.repliesFrom):
				self.writeln("recieved false reply"+str(n))
				result = False
		return result
			
	def setPos(self, pos):
		self.pos = pos


