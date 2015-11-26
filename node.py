import sys
import struct
import time
import select


from socket import *
from random import randint
from gui import MainWindow
from sensor import *
from neighbour import *





class Node(object):
	def __init__(self, address, position, radius, value):
		
		self.position = position
		self.range = radius
		self.value = value
		self.list = {}
		self.readable = None
		self.writeable = None
		self.exceptional = None

		# -- Create the multicast listener socket. --
		mcast = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)
		# Sets the socket address as reusable so you can run multiple instances
		# of the program on the same machine at the same time.
		mcast.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
		# Subscribe the socket to multicast messages from the given address.
		mreq = struct.pack('4sl', inet_aton(address[0]), INADDR_ANY)
		mcast.setsockopt(IPPROTO_IP, IP_ADD_MEMBERSHIP, mreq)
		if sys.platform == 'win32': # windows special case
			mcast.bind( ('localhost', address[1]) )
		else: # should work for everything else
			mcast.bind(address)

		self.mcast = mcast

		# -- Create the peer-to-peer socket. --
		peer = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)
		# Set the socket multicast TTL so it can send multicast messages.
		peer.setsockopt(IPPROTO_IP, IP_MULTICAST_TTL, 5)
		# Bind the socket to a random port.
		if sys.platform == 'win32': # windows special case
			peer.bind( ('localhost', INADDR_ANY) )
		else: # should work for everything else
			peer.bind( ('', INADDR_ANY) )

		self.peer = peer
		self.address = self.peer.getsockname()

	def addToList(self, neighbour):
		self.list[neighbour.address] = neighbour


	# [TODO] Sends a ping command to all other nodes
	def sendPing(self):
		message = message_encode(MSG_PING, 0, self.position, self.position)
	
		for c in self.writeable:
			print str(c.getsockname())
			c.sendto(message, self.mcast.getsockname())
			self.write("sending ping")
	


		# check distance
		# not too big?
		# Not myself (==0)
		# send pong to initiator

	def sendPong(self, sender):
		message = message_encode(MSG_PONG, 0, self.position, self.position)
		self.write(str(sender))
		# for c in self.writeable:
			# if c.getsockname()[1] == sender[1]:
		# self.peer.sendto(message, sender)
		self.write("pong to: " + str(sender))

	# Automatically select sockets to read and write from
	def updateSelect(self):
		self.readable, self.writeable, self.exceptional = select.select([self.mcast], [self.peer], [], 0)

	def updateNeighbours(self, sender):
		self.write("updateNeighbours " + str(sender[1]))

	def addWindow(self, window):
		self.window = window

	def write(self, message):
		self.window.writeln(message)














	
