import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)
import logging

from PyQt4 import QtCore

import log
# TODO: read settings from a logging.ini, where, basing on classname, level,
# style (colored,format), propagate and stream (that is, file/output) can be
# changed on a fine-grained level
logger = log.ColoredLogger(__name__)
from player import QtPlayer
from bobina import Bobina, get_libraries, find_libraries
from event import EventMonitor
from command import TCPCommandSocket, HTTPCommandSocket, short_command
from config_manager import get_config


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
        self.audio_source = EventAggregator()
        if get_config()['SOCKET_TCP']:
            self.tcp_socket = TCPCommandSocket(
                self, get_config()['SOCKET_TCP'])
        if get_config()['SOCKET_HTTP']:
            self.http_socket = HTTPCommandSocket(
                self, get_config()['SOCKET_HTTP'])

        self.player.empty.connect(self.on_empty)

    def start(self):
        self.on_empty()

    def on_empty(self):
        self.log.debug("Playlist empty, need to fill")

        next_audio = self.audio_source.get_next()
        assert type(next_audio) is list
        self.player.now_play_sequence(next_audio)


class EventAggregator(QtCore.QObject):
    '''
    EventManager knows what need to be played; it handles Bobina, listen to
    events.
    More abstractly, it's an Audio source that aggregates different Audio
    sources
    '''
    @log.cls_logger
    def __init__(self):
        QtCore.QObject.__init__(self)
        self.bobina = Bobina()
        self.event_monitor = EventMonitor()
        self.event_monitor.bell_now.connect(self.on_event)
        self.last_event = None
        self.paused = False

    def on_event(self, ev):
        self.log.info("Bell rang " + str(ev))
        if not self.paused:
            self.last_event = ev
        else:
            self.log.debug("Ignoring bell: we're in pause mode")

    def get_next(self):
        last = self.last_event
        self.last_event = None
        if last is None:
            next_audio = self.bobina.get_next()
            self.log.info("Next audio is %s, from Bobina" % next_audio)
            next_audio = [next_audio]
        else:
            next_audio = last.audio
            self.log.info("Next audio is %s, from Event %s" %
                          (next_audio, last))
        return next_audio

    def pause_events(self, value=None):
        if value is None:
            value = not self.paused
        self.paused = value

    @short_command("last_event")
    def cmd_lastevent(controller, args):
        return str(controller.audio_source.last_event)

    @short_command("pause_events")
    def cmd_pause_events(controller, args):
        controller.audio_source.pause_events()
        return str(controller.audio_source.paused)


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


def parse_options(args):
    # TODO: move to argparse
    opts = {'config': []}
    if len(args) > 1:
        opts['config'].append(args[1])
    return opts


if __name__ == '__main__':
    import sys
    #logging.basicConfig(filename=None, level=logging.DEBUG)
    opts = parse_options(sys.argv)
    log.ColoredLogger.default_level = logging.DEBUG
    logger.info('start')
    app = Tamarradio(sys.argv)
    app.connect(app, QtCore.SIGNAL('start_app()'), main)
    get_config().from_pyfile("default_config.py")
    get_config().from_pyfile("/etc/tamarradio/player.cfg", silent=True)
    for configfile in opts['config']:
        get_config().from_pyfile(configfile)
    for d in get_config()['LIBRARIES_PATH']:
        get_libraries().update(find_libraries(d))
    ret = app.exec_()
    logger.info('end %d' % ret)
    sys.exit(ret)
