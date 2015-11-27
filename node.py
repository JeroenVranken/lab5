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
	def __init__(self, mcast_addr, sensor_pos, sensor_range, sensor_val, win):
		self.pos = sensor_pos
		self.range = sensor_range
		self.val = sensor_val
		self.readable = None
		self.writeable = None
		self.exceptional = None
		self.window = win
		
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
			
	def writeln(self, string):
		self.window.writeln(string)
		
	def sendPing(self):
		message = message_encode(MSG_PING, 0, self.pos, self.pos)
		for c in self.writeable:
			c.sendto(message, self.mcast.getsockname())
			self.writeln("Send ping message")

	def sendPong(self, addr):
		message = message_encode(MSG_PONG, 0, self.pos, self.pos)
		self.peer.sendto(message,(addr[0], addr[1]))
		self.writeln("Send pong to: "+str(addr))
	
	def updateSelect(self):
		self.readable, self.writeable, self.exceptional = select.select([self.mcast], [self.peer], [], 0)

	def updateNeighbours(self, addr):
		self.write("updateNeighbours " + str(addr[1]))



