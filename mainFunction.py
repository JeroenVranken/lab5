## Netwerken en Systeembeveiliging Lab 5 - Distributed Sensor Network
## NAME: 			Jeroen Vranken & Mees Froberg
## STUDENT ID:			10658491   &   10559949
import sys
import struct
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
	print str(sensor_pos) + "\n"

	# -- make the gui --
	window = MainWindow()
	window.writeln( 'my address is %s:%s' % node.peer.getsockname() )
	window.writeln( 'my position is (%s, %s)' % sensor_pos )
	window.writeln( 'my sensor value is %s' % sensor_val )

	# -- This is the event loop. --
	while window.update():

		node.updateSelect()

		# Check for new messages
		for c in node.readable:
			# Receive message from server and write to the window
			message = c.recvfrom(1024)
			parseMessage(message, node)
			# window.write(str(message))

		# Check if something was entered in the GUI, parse the input and execute the corresponding command
		line = window.getline()
		if line:
			inputType = parseInput(line, node)
	
		# # Prevent busy looping
		time.sleep(0.1)

def parseInput(i, node):
	split = i.split(" ")
	if split[0] == "ping":
		node.sendPing()

def parseMessage(i, node):
	message = message_decode(i[0])
	sender = i[1]
	print "receiver: " + str(node.address[1]) + "sender: " + str(sender)
	print str(message)
	if message[0] == 0 and str(sender[1]) != str(node.address[1]):
		node.sendPong()

	# If received is pong, add to neighbour list
	elif message[0] == 1:
		node.updateNeighbours(sender)


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
