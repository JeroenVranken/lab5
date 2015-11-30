## Netwerken en Systeembeveiliging Lab 5 - Distributed Sensor Network
## NAME: 			Jeroen Vranken & Mees Froberg
## STUDENT ID:			10658491   &   10559949

import sys
import struct
import math
import time
import select

from socket import *
from random import randint
from gui import MainWindow
from sensor import *
from node import *

# Get random position in NxN grid.
def random_position(n):
	x = randint(0, n)
	y = randint(0, n)
	return (x, y)

def main(mcast_addr,
	sensor_pos, sensor_range, sensor_val,
	grid_size, ping_period):
	"""
	mcast_addr: udp multicast (ip, port) tuple.
	sensor_pos: (x,y) sensor position tuple.
	sensor_range: range of the sensor ping (radius).
	sensor_val: sensor value.
	grid_size: length of the  of the grid (which is always square).
	ping_period: time in seconds between multicast pings.
	"""
	
	# -- make the gui --
	window = MainWindow()
	
	# -- make the node --
	node = Node(mcast_addr, sensor_pos,sensor_range, sensor_val, window)
	
	start_time = time.time()


	# -- This is the event loop. --
	while window.update():
		node.updateSelect()
		
		# Auto ping
		if (time.time() - start_time) > ping_period:
			node.sendPing()
			start_time = time.time()


		# Check for new messages
		for c in node.readable:
			# Receive message from server and write to the window
			data = c.recvfrom(1024)
			parseData(data, node)
		
		# Check if something was entered in the GUI, parse the input and execute the corresponding command
		line = window.getline()
		if line:
			parseInput(line, node)
	
		# # Prevent busy looping
		time.sleep(0.1)

def parseInput(inp, node):
	split = inp.split(" ")
	if split[0] == "ping":
		node.sendPing()
	elif split[0] == "list":
		node.listNeighbours()
	elif split[0] == "echo":
		node.initiateEcho()
	elif split[0] == "pos":
		pos = (int(split[1]), int(split[2]))
		node.setPos(pos)

def parseData(data, node):
	m = message_decode(data[0])
	message = {}
	message['type'] = m[0]
	message['sequence'] = m[1]
	message['initiator'] = m[2]
	message['neighbour'] = m[3]
	message['addr'] = data[1]
	
	dist = calcDist(message['initiator'], node.pos)

	
	# message in range and not it's own message
	if dist <= node.range and dist != 0:
		
		# If received is a ping, send a pong
		if message['type'] == MSG_PING:
			node.sendPong(message['addr'])

		# If received is pong, add to neighbour list
		elif message['type'] == MSG_PONG:
			node.updateNeighbours(message['initiator'], message['addr'])

		elif message['type'] == MSG_ECHO:
			# node.writeln("message type = "+ str(message['type']))
			node.writeln("Received echo from "+ str(message['neighbour']))
			node.createWave(message)

		elif message['type'] == MSG_ECHO_REPLY:
			# node.writeln("message type = "+ str(message['type']))
			node.writeln("Received echo reply from "+ str(message['neighbour']))
			for w in node.wave:
				if message['sequence'] == w.sequence and message['initiator'] == w.initiator:
					w.addReply(message['neighbour'])
					if node.receivedAllReplies(w):
						node.writeln("receivedAllReplies!")
						node.sendEchoReply(w)

def calcDist(l1, l2):
	dif1 = abs(l1[0] - l2[0])
	dif2 = abs(l1[1] - l2[1])
	return math.sqrt((dif1**2)+(dif2**2))

# -- program entry point --
if __name__ == '__main__':
	import sys, argparse
	p = argparse.ArgumentParser()
	p.add_argument('--group', help='multicast group', default='224.1.1.1')
	p.add_argument('--port', help='multicast port', default=51274, type=int)
	p.add_argument('--pos', help='x,y sensor position', default=None)
	p.add_argument('--grid', help='size of grid', default=100, type=int)
	p.add_argument('--range', help='sensor range', default=50, type=int)
	p.add_argument('--value', help='sensor value', default=-1, type=int)
	p.add_argument('--period', help='period between autopings (0=off)',
		default=5, type=int)
	args = p.parse_args(sys.argv[1:])
	if args.pos:
		pos = tuple( int(n) for n in args.pos.split(',')[:2] )
	else:
		pos = random_position(args.grid)
	if args.value >= 0:
		value = args.value
	else:
		value = randint(0, 100)
	mcast_addr = (args.group, args.port)
	main(mcast_addr, pos, args.range, value, args.grid, args.period)
