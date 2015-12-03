## Netwerken en Systeembeveiliging Lab 5 - Distributed Sensor Network
## NAME: 			Jeroen Vranken & Mees Froberg
## STUDENT ID:			10658491   &   10559949
## Group: 11

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
			parseInput(line, node, grid_size)
	
		# Prevent busy looping
		time.sleep(0.1)

def parseInput(inp, node, grid_size):
	"""
	parses input that user entered in the GUI

	"""
	# Splits the input on spaces
	split = inp.split(" ")
	if split[0] == "ping":
		node.sendPing()
	
	elif split[0] == "list":
		node.listNeighbours()
	
	elif split[0] == "echo":
		node.initiateEcho(OP_NOOP)

	elif split[0] == "move":
		node.setPos(random_position(grid_size))
		node.writeln("Set position to: " + str(node.pos))
	
	elif split[0] == "set":
		newRange = int(split[1])
		possibleRange  = [20,30,40,50,60,70]
		
		if newRange not in possibleRange:
			node.writeln("Range must be set between 20 and 70, with increment of 10")
		else:
			node.range = newRange
			node.writeln("Range set to: " + str(node.range))
	
	elif split[0] == "size":
		node.initiateEcho(OP_SIZE)

	elif split[0] == "value":
		node.setVal(randint(0, 100))
		node.writeln("New sensor value = " + str(node.val))

	elif split[0] == "setvalue":
		node.setVal(int(split[1]))
		node.writeln("New sensor value = " + str(node.val))

	elif split[0] == "sum":
		node.initiateEcho(OP_SUM)

	elif split[0] == "same":
		node.initiateEcho(OP_SAME)

	elif split[0] == "min":
		node.initiateEcho(OP_MIN)

	elif split[0] == "max":
		node.initiateEcho(OP_MAX)

def parseData(data, node):
	"""
	Parses the received message, takes action based on the content of the message 
	
	"""

	m = message_decode(data[0])
	message = {}
	message['type'] = m[0]
	message['sequence'] = m[1]
	message['initiator'] = m[2]
	message['neighbour'] = m[3]
	message['operation'] = m[4]
	message['capability'] = m[5]
	message['payload'] = m[6]
	message['addr'] = data[1]
	
	dist = calcDist(message['neighbour'], node.pos)

	
	# message in range and not it's own message
	if dist <= node.range and dist != 0:
		
		# If received is a ping, send a pong
		if message['type'] == MSG_PING:
			node.sendPong(message['addr'])

		# If received is pong, add to neighbour list
		elif message['type'] == MSG_PONG:
			node.updateNeighbours(message['initiator'], message['addr'])

		# If message type is echo, create a new wave object
		elif message['type'] == MSG_ECHO:
			node.writeln("Received echo from "+ str(message['neighbour']) + " operation: " + str(message['operation']) + " capability: " + str(message['capability']) + ", payload: " + str(message['payload']))
			node.createWave(message)

		# if message type is echo reply, take action based on the operation
		elif message['type'] == MSG_ECHO_REPLY:

			node.writeln("Received echo reply from "+ str(message['neighbour']) + " operation: " + str(message['operation']) + " capability: " + str(message['capability']) + ", payload: " + str(message['payload']))
			
			# Loop over all wave objects assiociated with the node
			for w in node.wave:

				# Finds the wave corresponding to the message
				if message['sequence'] == w.sequence and message['initiator'] == w.initiator:
					w.addReply(message['neighbour'])
					w.setPayload(w.payload + int(message['payload']))
					w.setCapability(message['capability'])
					
					# Checks if all replies are received from each neigbour except the father
					if node.receivedAllReplies(w):
						node.writeln("Received all echo replies for sequence: " + str(message['sequence']))
						
						# Checks if the intial node of the wave has not been reached (prevents the initiator to send to itself)
						if w.fatherAddr != None:
							node.sendEchoReply(w)
						
						# The inital node has been reached
						else:
							if int(message['operation']) == OP_NOOP:
								node.writeln("ECHO WAVE " + str(message['sequence']) + " COMPLETED!")
							
							elif int(message['operation']) == OP_SIZE:
								w.incrementPayload()
								node.writeln("Network size: " + str(w.payload))
							
							elif int(message['operation']) == OP_SUM:
								w.setPayload(w.payload + node.val)
								node.writeln("Network sum: " + str(w.payload))
							
							elif int(message['operation']) == OP_SAME:
								w.incrementPayload()
								if w.payload > 1:
									node.writeln("There are " + str(w.payload) + " nodes with the value: " + str(node.val))
								else:
									node.writeln("There is " + str(w.payload) + " node with the value: " + str(node.val))
							
							elif int(message['operation']) == OP_MIN:
								node.writeln("The minimum sensor value is: " + str(w.capability))
							
							elif int(message['operation']) == OP_MAX:
								node.writeln("The maximum sensor value is: " + str(w.capability))


# Calculates euclidian distance between two (X, Y) positions
def calcDist(l1, l2):
	dif1 = abs(l1[0] - l2[0])
	dif2 = abs(l1[1] - l2[1])
	return math.sqrt((dif1**2)+(dif2**2))

# -- program entry point --
if __name__ == '__main__':
	import sys, argparse
	p = argparse.ArgumentParser()
	p.add_argument('--group', help='multicast group', default='224.1.1.1')
	p.add_argument('--port', help='multicast port', default=51275, type=int)
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
