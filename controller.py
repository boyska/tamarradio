import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)
import logging

from PyQt4 import QtCore

import log
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
        self.event_monitor = EventMonitor(self)
        self.event_monitor.bell_now.connect(self.on_event)
        self.player.empty.connect(self.on_empty)

        self.last_event = None

    def start(self):
        self.on_empty()

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
