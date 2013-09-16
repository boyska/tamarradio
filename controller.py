import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)
import logging

from PyQt4 import QtCore, QtNetwork

import log
# TODO: read settings from a logging.ini, where, basing on classname, level,
# style (colored,format), propagate and stream (that is, file/output) can be
# changed on a fine-grained level
logging.setLoggerClass(log.ColoredLogger)
logger = logging.getLogger(__name__)
from player import QtPlayer
from bobina import Bobina
from event import EventMonitor


class Controller(QtCore.QObject):
    '''all the main logic, without those boring details'''
    # when a Event rings
    event_occurred = QtCore.pyqtSignal()
    song_finished = QtCore.pyqtSignal()
    # just before exiting, to do some cleaning
    closing = QtCore.pyqtSignal()

    @log.cls_logger
    def __init__(self):
        QtCore.QObject.__init__(self)
        self.log.debug("%s instantiating" % self.__class__.__name__)
        self.player = QtPlayer()
        self.bobina = Bobina()
        self.event_monitor = EventMonitor()
        self.socket = QtNetwork.QTcpServer()

        self.event_monitor.bell_now.connect(self.on_event)
        self.player.empty.connect(self.on_empty)
        self.socket.newConnection.connect(self.on_socket_message)

        self.last_event = None

    def start(self):
        self.on_empty()
        self.socket.listen(QtNetwork.QHostAddress.LocalHost, 9999)

    def on_event(self, ev):
        self.log.info("Bell rang " + str(ev))
        self.last_event = ev

    def on_empty(self):
        self.log.debug("Playlist empty, need to fill")
        last = self.last_event
        self.last_event = None
        if last is None:
            next_audio = self.bobina.get_next()
            self.log.info("Next audio is %s, from Bobina" % next_audio)
        else:
            next_audio = last.audio
            self.log.info("Next audio is %s, from Event %s" %
                          (next_audio, last))

        self.player.now_play(next_audio)

    def on_socket_message(self):
        conn = self.socket.nextPendingConnection()

        def handle_read():
            try:
                msg = conn.readAll()
                command = msg.data().decode('utf-8').strip().split(' ', 1)[0]
                #TODO: move processing to pluggable Command objects
                if command == 'info':
                    ret = 'Playing: %s' % self.player
                if command == 'next_event':
                    ret = str(self.last_event)
                else:
                    ret = 'Unsupported command: %s' % command
                conn.write(ret)
            except:
                conn.write("Errors processing request")
            finally:
                conn.disconnectFromHost()

        conn.readyRead.connect(handle_read)


class Tamarradio(QtCore.QCoreApplication):
    started = QtCore.pyqtSignal()

    def __init__(self, *args):
        self.args = args
        QtCore.QCoreApplication.__init__(self, *args)
        self.setApplicationName('tamarradio')
        QtCore.QTimer.singleShot(1000, self, QtCore.SIGNAL('really_run()'))
        QtCore.QTimer.singleShot(0, self, QtCore.SIGNAL('start_app()'))

_c = None


def main():
    global _c
    _c = Controller()
    app.connect(app, QtCore.SIGNAL('really_run()'), _c.start)

if __name__ == '__main__':
    import sys
    #logging.basicConfig(level=logging.DEBUG)
    logger.info('start')
    app = Tamarradio(sys.argv)
    app.connect(app, QtCore.SIGNAL('start_app()'), main)
    ret = app.exec_()
    logger.info('end %d' % ret)
    sys.exit(ret)
