import sys
import SocketServer

import logging
logging.basicConfig(level=logging.DEBUG)

"""
TODO: definire in maniera completa come e' possibile interagire 
con il controller per definire le funzioni accettate.
"""

CODE_OK = 200
CODE_ERR = 500

# This class manage TCP Requests 
class MyTCPHandler(SocketServer.BaseRequestHandler):
	def __init__(self, callback, *args, **keys):
		self.callback = callback
		SocketServer.BaseRequestHandler.__init__(self, *args, **keys)

	def handle(self):  	
		self.data = self.request.recv(1024).strip()
		print "{} wrote:".format(self.client_address[0])
		print self.data

    # Execute command 		
		retmsg = self.callback( self.data )
		
    # Return resuts 		
		self.request.sendall( str(retmsg) )
		
"""
the foo() class emulate the controller; 
action is executed once a message is recived 
"""
class foo():
  def __init__(self): 
    self.cmdmapper = {
        'stop': self.stop,
        'play': self.play,
        'pause': self.stop, # ? i'm not sure
        'help': self.help
      }

  def help(self, *args):
    print "Available commands:"
    for i in self.cmdmapper.keys():
      print "%s()" % i
    return CODE_OK
      
  def stop(self, *args):
    logging.info("STOP PLAYER")
    return CODE_OK
    
  def play(self, *args):
    logging.info("PLAY PLAYER")
    return CODE_OK
    
  def action(self, command):
    logging.info( "Received " + command )
    try:
      cmd, parameter = command.split(" ",1)
    except:
      cmd = command    
      parameter = ""
    
    logging.info("Cmd: %s - Param %s" % (cmd, parameter) )
    
    if not self.cmdmapper.has_key( cmd ):
      logging.error("Command not found!")
      return CODE_ERR

    # Return the return values of the function
    return self.cmdmapper[ cmd ]( parameter )


def handler_factory(callback):
	def createHandler(*args, **keys):
		return MyTCPHandler(callback, *args, **keys)
	return createHandler


# TEST CODE
if __name__ == "__main__":
	
	f = foo() 

	HOST, PORT = "localhost", 9999
	server =   SocketServer.TCPServer((HOST, PORT), handler_factory( f.action ) ) 
	logging.info("Starting server %s:%s (press CTRL+C to shutdown)" % ( HOST, PORT) )
	server.serve_forever()

