import os
from datetime import datetime
import functools
from heapq import heappush, heappop
from collections import defaultdict
import logging
logger = logging.getLogger(__name__)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from PyQt4 import QtCore

from log import cls_logger
from config_manager import get_config
import tamarradb
import cacheutils


def time_parse(s):
    return datetime.strptime(s, r'%Y-%m-%d-%H-%M-%S')


@functools.total_ordering
class Bell:
    '''
    A Bell is a time-audio coupling.
    The audio must be ready to be played.

    There is a total ordering on Bells, which just reflects the natural
    ordering on their time; you can also compare Bells to datetime.

    A Bell is tipically produced by an EventLoader and consumed by an
    EventMonitor.
    '''
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


class DirEventLoader(QtCore.QObject):
    '''
    A generic EventLoader has two duties:
    * discovering new events definition (on rescan, which could be manually
      invoked, or called by inotify)
    * produces ready-to-play Bells (that is, their action is not anymore
      dependent on slow I/O operations such as network access) and emit
      bell_ready accordingly

    This implementation of an EventLoader scans a directory for specially-named
    files.
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


class DBEventLoader(QtCore.QObject):
    bell_ready = QtCore.pyqtSignal(Bell)

    @cls_logger
    def __init__(self):
        QtCore.QObject.__init__(self)
        logger.debug("%s instantiating" % self.__class__.__name__)
        #TODO: self.connection = config.boh
        self.engine = create_engine(get_config()['DB'])
        tamarradb.Base.metadata.create_all(self.engine)
        self.visited = defaultdict(lambda: None)  # id-on-db: datetime

    def schedule_next(self, ev, force=False):
        '''
        Questo metodo controlla se l'evento specificato dall'id deve suonare
        anche nel futuro, e in caso predispone entrambi i timer (quello verso
        noi stessi e quello verso il BellCacher
        '''

        session = sessionmaker(bind=self.engine)()

        def get_timer(t):
            '''
            Ritorna un Qtimer che suona al tempo t
            (NON tra t secondi)
            '''
            delta = t - datetime.now()
            timer = QtCore.QTimer()
            timer.setInterval(delta.total_seconds() * 1000)
            timer.setSingleShot(True)
            timer.start()
            return timer

        if force:
            ev = session.query(tamarradb.Event).filter_by(id=id).first()
        if ev is None:  # L'evento non esiste
            self.log.info("L'evento [%d] non e' piu' sul db" % ev.id)
            return
        event_time = ev.alarm.next_ring()
        if event_time < (datetime.now() + get_config().CACHING_TIME):
            return
        get_timer(event_time).timeout.connect(
            lambda x: self.schedule_next(id, True))
        cacher = BellCacher(ev.action, event_time)
        # TODO: una funzione che controlla se il tutto esiste ancora; dobbiamo
        # definirla noi per fare dependency inversion
        cacher.checker = None
        cacher.ready = self.bell_ready.emit
        get_timer(event_time - get_config().CACHING_TIME).\
            timeout.connect(cacher.run)

    def rescan(self):
        # Durante lo scan, facciamo partire due eventi:
        # uno a ev.next_ring() che va verso noi stessi, e serve per verificare
            # se l'evento ha una ripetitivita' ed agire di conseguenza
        # l' altro ev.next_ring()-CACHING_TIME, va verso un BellCacher, ovvero
        # un accrocchio che quando si sveglia cacha l'audio (producendo dunque
        # un Bell) e lo passa al monitor

        session = sessionmaker(bind=self.engine)()
        for event in session.query(tamarradb.Event):
            self.schedule_next(event)


class BellCacher(QtCore.QObject):
    @cls_logger
    def __init__(self, action, time):
        self.action = action
        self.time = time
        self.checker = None
        self.ready = None

    def run(self):
        if self.checker is not None:
            if self.checker() is not True:
                self.log.info("Check falsed for action %s" % self.action)
                return
        self.log.debug("Caching %s" % self.action)
        for path in self.action.get_audio(None):  # TODO: vanno passate le libraries!
            cached = cacheutils.safecopy(path)
            b = Bell(self.time, cached)
            if self.ready is not None:
                self.ready(b)


class EventMonitor(QtCore.QObject):
    '''
    An EventMonitor emits "bell_now" signals when an event is occurring.

    It does not know anything about current playing audio; and it will _always_
    trigger bells at the correct time. Its duty of the EventAggregator to
    decide whether the current song should be stopped or not.
    '''
    bell_now = QtCore.pyqtSignal(Bell)

    @cls_logger
    def __init__(self):
        QtCore.QObject.__init__(self)
        self.log.debug("%s instantiating" % self.__class__.__name__)
        self.event_loaders = [DirEventLoader(), DBEventLoader()]

        self.waiting_bell = None
        self.current_timer = None

        self.bell_queue = []  # it's a heap!
        for loader in self.event_loaders:
            loader.bell_ready.connect(self.on_bell_ready)
            loader.rescan()

    def on_timer_expired(self):
        self.bell_now.emit(self.waiting_bell)
        while self.bell_queue and self.bell_queue[0] < datetime.now():
            b = heappop(self.bell_queue)
            self.bell_now.emit(b)
        self.waiting_bell = None
        self.check_timers()

    def on_bell_ready(self, eventid, bell):
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
