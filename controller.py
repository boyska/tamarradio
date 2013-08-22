import heapq
import logging
logger = logging.getLogger(__name__)

from PyQt4 import QtCore

from player import QtPlayer
from bobina import Bobina
import config
from event import Event


def get_config():
    return config


class EventMonitor(QtCore.QObject):
    event_now = QtCore.pyqtSignal(Event)

    def __init__(self, controller):
        self.controller = controller
        self.worker = None  # maintain a LoaderWorker
        self.worker.event_ready.connect(self.handle_event)
        self.event_queue = []

        for i in range(get_config().preload_number):
            self.preload_another()

        self.events = []  # heapq of ALL events
        #TODO: load events

    def preload_another(self):
        #TODO: refresh list of events
        if not self.events:
            logger.debug("No events")
            return
        ev = heapq.heappop(self.events)
        logger.debug("Preloading %s; queuing" % str(ev))
        self.worker_queue.push(ev)

    #TODO: gestisci gli eventi e i loro timer
    def handle_event(self, event):
        heapq.heappush(self.event_queue, event)


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
