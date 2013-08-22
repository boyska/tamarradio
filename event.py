import os
from datetime import datetime
import functools
import heapq
import logging
logger = logging.getLogger(__name__)

from PyQt4 import QtCore

from controller import get_config


def time_parse(s):
    return datetime.strptime(s, r'%Y-%m-%d-%H-%M-%S')


class EventLoader:
    '''Discovers new events definition and produces ready-to-play Bells (that
    is, their action is not dependent on slow I/O operations such as network
    access)'''
    new_event = QtCore.pyqtSignal()

    def __init__(self, path):
        self.events = set()
        self.path = path
        self.events.update(self.rescan())

    def rescan(self):
        for d in self.path:
            for root, subfolders, files in os.walk(d):
                for f in files:
                    #the filename is the event date
                    #the content is the audio itself
                    #(event specification is yet to come)
                    if f.split('.')[-1].lower() in ('.wav', '.mp3', '.ogg'):
                        try:
                            base = f.split('.')[1]
                            date = time_parse(base)
                            ev = Bell(date, os.path.join(root, f))
                            if ev not in self.events:
                                self.new_event(ev)
                        except Exception as exc:
                            logger.debug("Event %s skipped: %s" % (f, exc))
                            pass


@functools.total_ordering
class Bell:
    def __init__(self, alarm, action):
        self.alarm = alarm
        self.action = action

    def __lt__(self, other):
        # a duck is crying for this "isinstance"
        # wait: it's not a duck, but it squaws like a duck...
        if(isinstance(other, datetime)):
            return self.alarm < other
        return self.alarm < other.alarm

    def __str__(self):
        return 'Event <%s, %s>' % (self.name, str(self.time))


class EventMonitor(QtCore.QObject):
    '''When a new ready-to-play Event is available, handle it: that is, trigger
    its alarm at the right moment
    '''
    event_now = QtCore.pyqtSignal(Bell)

    def __init__(self, controller):
        self.controller = controller
        self.worker = None  # maintain a LoaderWorker
        self.worker.event_ready.connect(self.handle_event_ready)
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
    def handle_event_ready(self, event):
        heapq.heappush(self.event_queue, event)
