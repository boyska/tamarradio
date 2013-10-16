from PyQt4 import QtNetwork
from http.server import BaseHTTPRequestHandler
from http.client import HTTPMessage, responses
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
            args = msg.data().decode('utf-8').strip().split(' ', 1)
            command = args.pop(0)
            if command in short_commands:
                ret = short_commands[command](self.controller, args)
                conn.write(ret)
        except Exception as exc:
            conn.write("Errors processing request\n%s" % exc)
        finally:
            conn.disconnectFromHost()

    def on_socket_message(self):
        conn = self.socket.nextPendingConnection()
        conn.readyRead.connect(lambda: self.handle_read(conn))


class HTTPCommandSocket(TCPCommandSocket):
    def handle_read(self, conn):
        m = HTTPMessage()
        status = 200
        try:
            msg = conn.readAll()
            request = HTTPRequest(bytes(msg))
            if request.path.startswith('/command/'):
                command = request.path.split('/')[2]
                args = request.path.split('/')[3:]
                if command not in short_commands:
                    status = 405
                    m.set_payload('command not found').as_string()
                ret = short_commands[command](self.controller, args)
                m.set_payload(ret)
            else:
                status = 405
                m.set_payload('invalid route')
        except Exception as exc:
            #TODO: 500 error
            status = 500
            m.set_payload('error!')
            raise exc
        finally:
            conn.write('HTTP/1.1 %d %s\n%s' %
                       (status, responses[status], m.as_string()))
            conn.disconnectFromHost()
