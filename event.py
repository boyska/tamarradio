import os
from datetime import datetime
import functools
from heapq import heappush, heappop
import logging
logger = logging.getLogger(__name__)

from PyQt4 import QtCore


def time_parse(s):
    return datetime.strptime(s, r'%Y-%m-%d-%H-%M-%S')


@functools.total_ordering
class Bell:
    def __init__(self, alarm, audio):
        self.alarm = alarm
        self.audio = audio

    def __lt__(self, other):
        # a duck is crying for this "isinstance"
        # wait: it's not a duck, but it squaws like a duck...
        if(isinstance(other, datetime)):
            return self.alarm < other
        if self.alarm < other.alarm:
            return True
        if self.alarm > other.alarm:
            return False

        return hash(self.audio) < hash(other.audio)

    def __str__(self):
        return 'Bell <%s, %s>' % (self.audio, str(self.time))


class EventLoader:
    '''Discovers new events definition and produces ready-to-play Bells (that
    is, their action is not dependent on slow I/O operations such as network
    access)'''
    bell_ready = QtCore.pyqtSignal()

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
                                self.bell_ready(ev)
                        except Exception as exc:
                            logger.debug("Event %s skipped: %s" % (f, exc))
                            pass


class EventMonitor(QtCore.QObject):
    '''When a new ready-to-play Bell is available, handle it: that is, trigger
    its alarm at the right moment
    '''
    bell_now = QtCore.pyqtSignal(Bell)

    def __init__(self, controller):
        self.controller = controller
        self.event_loader = EventLoader(self)
        self.event_loader.bell_ready.connect(self.on_bell_ready)

        self.bell_queue = []

        self.waiting_bell = None
        self.current_timer = None

    def on_timer_expired(self, timer):
        self.bell_now.emit(self.waiting_bell)
        while self.bell_queue[0] < datetime.now():
            self.bell_now.emit(heappop(self.bell_queue))
        self.check_timers()

    def on_bell_ready(self, bell):
        if bell.time < datetime.now():  # + timedelta(seconds=10)
            return
        heappush(self.bell_queue, bell)
        self.check_timers()

    def check_timers(self):
        def set_timer(bell):
            delta = bell.time - datetime.now()
            self.current_timer = QtCore.QTimer()
            self.current_timer.setInterval(delta)
            self.current_timer.setSingleShot(True)
            self.waiting_bell = bell
            self.current_timer.start()

        if self.waiting_bell is None:
            if self.bell_queue:
                set_timer(heappop(self.bell_queue))
        else:
            if self.bell_queue and self.bell_queue[0] < self.waiting_bell:
                self.current_timer.stop()
                set_timer(heappop(self.bell_queue))
