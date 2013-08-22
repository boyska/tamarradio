import logging
logger = logging.getLogger(__name__)

from PyQt4 import QtCore

from player import QtPlayer
from bobina import Bobina
import config
from event import EventMonitor


def get_config():
    return config


class Controller(QtCore.QObject):
    '''all the main logic, without those boring details'''
    # when a Event rings
    event_occurred = QtCore.pyqtSignal()
    song_finished = QtCore.pyqtSignal()
    # just before exiting, to do some cleaning
    closing = QtCore.pyqtSignal()

    def __init__(self):
        self.event_monitor = EventMonitor(self)
        self.event_monitor.event_now.connect(self.on_event)
        self.player = QtPlayer()
        self.player.empty.connect(self.on_empty)
        self.bobina = Bobina()

        self.last_event = None

    def on_event(self, ev):
        self.last_event = ev

    def on_empty(self):
        last = self.last_event
        self.last_event = None
        if last is None:
            next_audio = self.bobina.get_next()
            logger.info("Next song is from Bobina")
        else:
            next_audio = last.get_audio()
            logger.info("Next song is audio %s from event %s" %
                        (next_audio, last))

        self.player.now_play(next_audio)
