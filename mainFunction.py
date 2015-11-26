## Netwerken en Systeembeveiliging Lab 5 - Distributed Sensor Network
## NAME: 			Jeroen Vranken & Mees Froberg
## STUDENT ID:			10658491   &   10559949
import sys
import struct
import math
from socket import *
from random import randint
from gui import MainWindow
from node import *
from sensor import *
import time
import select


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

	# initialize node
	node = Node(mcast_addr, sensor_pos,sensor_range, sensor_val)

	# -- make the gui --
	window = MainWindow()
	window.writeln( 'my address is %s:%s' % node.peer.getsockname() )
	window.writeln( 'my position is (%s, %s)' % sensor_pos )
	window.writeln( 'my sensor value is %s' % sensor_val )

	node.addWindow(window)

	# -- This is the event loop. --
	while window.update():

		node.updateSelect()

		# Check for new messages
		for c in node.readable:
			node.write("readable loop")

			# Receive message from server and write to the window
			message = c.recvfrom(1024)
			parseMessage(message, node)

		# Check if something was entered in the GUI, parse the input and execute the corresponding command
		line = window.getline()
		if line:
			parseInput(line, node)
	
		# # Prevent busy looping
		time.sleep(0.1)

def parseInput(i, node):
	split = i.split(" ")
	if split[0] == "ping":
		node.sendPing()


def parseMessage(i, node):
	decodedI = message_decode(i[0])
	# node.write(str(senderIP))
	mes = {}
	mes['type'] = decodedI[0]
	mes['sequence'] = decodedI[1]
	mes['initiator'] = decodedI[2]
	mes['neighbour'] = decodedI[3]
	mes['senderIP'] = i[1]

	dist = calcDist(mes['initiator'], node.position)
	if dist <= node.range: # message in range
		node.write("in range")
		node.write("distance " + str(dist))
		if dist != 0: # not it's own message
			node.write(mes['type'])
			if mes['type'] == MSG_PING:
				node.sendPong(mes['senderIP'])
				node.write("Ping message from sender: " + str(mes['initiator']))

			# If received is pong, add to neighbour list
			elif mes['type'] == MSG_PONG:
				node.updateNeighbours(mes['initiator'])
				node.write("Pong message from sender: " + str(mes['initiator']))



def calcDist(l1, l2):
	dif1 = abs(l1[0] - l2[0])
	dif2 = abs(l1[1] - l2[1])
	return math.sqrt((dif1**2)+(dif2**2))

# -- program entry point --
if __name__ == '__main__':
	import sys, argparse
	p = argparse.ArgumentParser()
	p.add_argument('--group', help='multicast group', default='224.1.1.1')
	p.add_argument('--port', help='multicast port', default=51525, type=int)
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
