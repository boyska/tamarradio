import sys
import SocketServer

import logging
logging.basicConfig(level=logging.DEBUG)

class MyTCPHandler(SocketServer.BaseRequestHandler):
	def __init__(self, callback, *args, **keys):
		self.callback = callback
		SocketServer.BaseRequestHandler.__init__(self, *args, **keys)

	def handle(self):
  	# self.request is the TCP socket connected to the client
		self.data = self.request.recv(1024).strip()
		print "{} wrote:".format(self.client_address[0])
		print self.data
		# just send back the same data, but upper-cased
		self.request.sendall(self.data.upper())
		self.callback()

# the foo() class emulate the controller; action is executed once 
class foo():
	def __init__(self): pass

	def action(self):
		print "Foo action"

def handler_factory(callback):
	def createHandler(*args, **keys):
		return MyTCPHandler(callback, *args, **keys)
	return createHandler

if __name__ == "__main__":
	
	f = foo()
	
	HOST, PORT = "localhost", 9999

  # Create the server, binding to localhost on port 9999
	# server = SocketServer.TCPServer((HOST, PORT), MyTCPHandler)
	server =   SocketServer.TCPServer((HOST, PORT), handler_factory( f.action ) ) 

	# logging.debug("Starting server %s:%s " % HOST, PORT )
	# Activate the server; this will keep running until you
	# interrupt the program with Ctrl-C
	server.serve_forever()

