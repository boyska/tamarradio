import os
from datetime import datetime
import functools
from heapq import heappush, heappop
import logging
logger = logging.getLogger(__name__)
from log import cls_logger

from PyQt4 import QtCore

from config_manager import get_config


def time_parse(s):
    return datetime.strptime(s, r'%Y-%m-%d-%H-%M-%S')


@functools.total_ordering
class Bell:
    def __init__(self, time, audio):
        self.time = time
        self.audio = audio

    def __lt__(self, other):
        # a duck is crying for this "isinstance"
        # wait: it's not a duck, but it squaws like a duck...
        if(isinstance(other, datetime)):
            return self.time < other
        if self.time < other.time:
            return True
        if self.time > other.time:
            return False

        return hash(self.audio) < hash(other.audio)

    def __str__(self):
        return 'Bell <%s, %s>' % (self.audio, str(self.time))


class EventLoader(QtCore.QObject):
    '''
    It has two duties:
    * discovering new events definition (on rescan, which could be manually
      invoked, or called by inotify)
    * produces ready-to-play Bells (that is, their action is not anymore
      dependent on slow I/O operations such as network access) and emit
      bell_ready accordingly
    '''
    # Note: bell_ready is NOT emitted at the time specified by the alarm;
    # instead, it is emitted whem its data is cached; it could be long before
    # the actual time of the alarm.
    bell_ready = QtCore.pyqtSignal(Bell)

    @cls_logger
    def __init__(self):
        QtCore.QObject.__init__(self)
        logger.debug("%s instantiating" % self.__class__.__name__)
        # TODO: self.libraries = \
        # {dir, AudioLibrary(dir) for dir in os.listdir(config.libraries)}
        self.events = set()
        self.path = get_config()['EVENTS_PATH']
        self.watch = QtCore.QFileSystemWatcher()
        for d in self.path:
            self.watch.addPath(d)
        self.watch.directoryChanged.connect(self.on_change)

    def on_change(self, what):
        self.log.info("Event dir changed!")
        self.rescan()

    def rescan(self):
        self.log.debug("scanning event path")
        for d in self.path:
            for root, subfolders, files in os.walk(d):
                for f in files:
                    #the filename is the event date
                    #the content is the audio itself
                    #(event specification is yet to come)
                    if f.split('.')[-1].lower() in ('wav', 'mp3', 'ogg'):
                        try:
                            base = f.split('.')[0]
                            date = time_parse(base)
                            ev = Bell(date, os.path.join(root, f))
                            if ev > datetime.now() and ev not in self.events:
                                #TODO: worker!
                                self.bell_ready.emit(ev)
                                self.log.info("event found in %s: %s" %
                                              (f, ev))
                        except Exception as exc:
                            self.log.debug("Event %s skipped: %s" % (f, exc))
                            pass


class EventMonitor(QtCore.QObject):
    '''
    When a new ready-to-play Bell is available, handle it: that is, trigger
    its alarm at the right moment

    It does not know anything about current playing audio; and it will _always_
    trigger bells at the correct time. Its duty of the Controller to decide
    whether the current song should be stopped or not.
    '''
    bell_now = QtCore.pyqtSignal(Bell)

    @cls_logger
    def __init__(self):
        QtCore.QObject.__init__(self)
        self.log.debug("%s instantiating" % self.__class__.__name__)
        self.event_loader = EventLoader()

        self.waiting_bell = None
        self.current_timer = None

        self.bell_queue = []  # it's a heap!
        self.event_loader.bell_ready.connect(self.on_bell_ready)
        self.event_loader.rescan()

    def on_timer_expired(self):
        self.bell_now.emit(self.waiting_bell)
        while self.bell_queue and self.bell_queue[0] < datetime.now():
            self.bell_now.emit(heappop(self.bell_queue))
        self.waiting_bell = None
        self.check_timers()

    def on_bell_ready(self, bell):
        self.log.debug("new bell ready: %s" % bell)
        if bell.time < datetime.now():  # + timedelta(seconds=10)
            self.log.debug("bell was too old! %s" % bell)
            return
        heappush(self.bell_queue, bell)
        self.check_timers()

    def check_timers(self):
        if not self.bell_queue:
            return

        def set_timer(bell):
            delta = bell.time - datetime.now()
            self.current_timer = QtCore.QTimer()
            self.current_timer.setInterval(delta.total_seconds() * 1000)
            self.current_timer.setSingleShot(True)
            self.waiting_bell = bell
            self.current_timer.timeout.connect(self.on_timer_expired)
            self.current_timer.start()
            self.log.debug("new timer set: %s (-%d s)" %
                           (str(bell.time), delta.total_seconds()))

        if self.waiting_bell is None:
            set_timer(heappop(self.bell_queue))
        else:
            if self.bell_queue[0] < self.waiting_bell:
                self.current_timer.stop()
                set_timer(heappop(self.bell_queue))
