from PyQt4 import QtNetwork
from http.server import BaseHTTPRequestHandler
from http.client import HTTPMessage
from io import BytesIO

short_commands = {}  # name: function


def short_command(name):
    def decorator(f):
        short_commands[name] = f
        return f
    return decorator


@short_command("info")
def cmd_info(controller, args):
    if hasattr(controller.player, 'get_now_playing'):
        return 'Playing: %s' % controller.player.get_now_playing()
    return 'Playing: %s' % controller.player


@short_command("next_event")
def cmd_nextevent(controller, args):
    return str(controller.last_event)


class HTTPRequest(BaseHTTPRequestHandler):
    def __init__(self, request_text):
        self.rfile = BytesIO(request_text)
        self.raw_requestline = self.rfile.readline()
        self.error_code = self.error_message = None
        self.parse_request()

    def send_error(self, code, message):
        self.error_code = code
        self.error_message = message


class TCPCommandSocket:
    def __init__(self, controller, port):
        self.socket = QtNetwork.QTcpServer()
        self.controller = controller
        self.socket.newConnection.connect(self.on_socket_message)
        self.socket.listen(QtNetwork.QHostAddress.LocalHost, port)

    def handle_read(self, conn):
        try:
            msg = conn.readAll()
            command = msg.data().decode('utf-8').strip().split(' ', 1)[0]
            #TODO: move processing to pluggable Command objects
            if command == 'info':
                ret = 'Playing: %s' % self.controller.player
            elif command == 'next_event':
                ret = str(self.controller.last_event)
            else:
                ret = 'Unsupported command: "%s"' % command
            conn.write(ret)
        except:
            conn.write("Errors processing request")
        finally:
            conn.disconnectFromHost()

    def on_socket_message(self):
        conn = self.socket.nextPendingConnection()
        conn.readyRead.connect(lambda: self.handle_read(conn))


class HTTPCommandSocket(TCPCommandSocket):
    def handle_read(self, conn):
        m = HTTPMessage()
        try:
            msg = conn.readAll()
            request = HTTPRequest(bytes(msg))
            if request.path.startswith('/command/'):
                command = request.path.split('/')[2]
                args = request.path.split('/')[3:]
                if command not in short_commands:
                    m.set_payload('command not found').as_string()
                ret = short_commands[command](self.controller, args)
                m.set_payload(ret)
            else:
                m.set_payload('invalid route')
        except Exception as exc:
            #TODO: 500 error
            m.set_payload('error!')
            raise exc
        finally:
            conn.write('HTTP/1.1 200 OK\n%s' % m.as_string())
            conn.disconnectFromHost()

