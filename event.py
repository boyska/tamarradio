import os
from datetime import datetime, timedelta
import functools
from heapq import heappush, heappop
from collections import defaultdict
import logging
logger = logging.getLogger(__name__)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from PyQt4 import QtCore

from log import cls_logger
from bobina import get_libraries
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

    def reload_event(self, id, bell):
        cls, filename = id.split('-', 2)
        if cls != self.__class__.__name__:
            return
        self.log.debug("Reloading %s but will no more play" % filename)

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
                            bell = Bell(date, os.path.join(root, f))
                            if bell > datetime.now() and \
                               bell not in self.events:
                                #TODO: BellCacher
                                self.log.info("event found in %s: %s" %
                                              (f, bell))
                                self.bell_ready.emit(bell)
                                self.store.add(self.__class__.__name__ + '-'
                                               + f, bell)
                        except Exception as exc:
                            self.log.debug("Event %s skipped: %s" % (f, exc))
                            pass


class DBEventLoader(QtCore.QObject):
    bell_ready = QtCore.pyqtSignal(Bell)

    @cls_logger
    def __init__(self):
        QtCore.QObject.__init__(self)
        self.log.debug("%s instantiating" % self.__class__.__name__)
        #TODO: self.connection = config.boh
        self.engine = create_engine(get_config()['DB'])
        tamarradb.Base.metadata.create_all(self.engine)
        self.visited = defaultdict(lambda: None)  # id-on-db: datetime
        self.running_cachers = [] # they are here because they need not to expire

    def schedule_next(self, ev, force=False):
        '''
        Questo metodo controlla se l'evento specificato dall'id deve suonare
        anche nel futuro, e in caso predispone entrambi i timer (quello verso
        noi stessi e quello verso il BellCacher
        '''

        session = sessionmaker(bind=self.engine)()

        def get_timer(t):
            '''
            Ritorna un QTimer che suona al tempo t
            (NON tra t secondi)
            '''
            delta = t - datetime.now()
            timer = QtCore.QTimer()
            timer.setInterval(delta.total_seconds() * 1000)
            timer.setSingleShot(True)
            return timer

        if force:
            ev = session.query(tamarradb.Event).filter_by(id=ev.id).first()
        if ev is None:  # L'evento non esiste
            self.log.info("L'evento [%d] non e' piu' sul db" % ev.id)
            return
        now = datetime.now()
        event_time = ev.alarm.next_ring(
            now + timedelta(seconds=get_config()['CACHING_TIME']))
        self.log.debug("Suona alle %s, sono le %s (tra %d secondi)" %
                      (event_time, now, (event_time-now).total_seconds()))
        assert event_time > \
            (datetime.now() + timedelta(seconds=get_config()['CACHING_TIME']))

        cacher = BellCacher(ev.action, event_time)
        cacher.reschedule = get_timer(event_time)
        self.connect(cacher.reschedule, QtCore.SIGNAL('timeout()'),
                     functools.partial(self.schedule_next, ev, True))
        cacher.reschedule.start()
        # TODO: una funzione che controlla se il tutto esiste ancora; dobbiamo
        # definirla noi per fare dependency inversion
        cacher.checker = None
        cacher.ready.connect(lambda b: self.bell_ready.emit(b))
        cacher.timer = get_timer(event_time -
                              timedelta(seconds=get_config()['CACHING_TIME']))
        cacher.timer.timeout.connect(cacher.run)
        cacher.timer.start()
        self.running_cachers.append(cacher)

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
    '''
    From (action, time) creates a cached action.
    Can be provided with a checker; a function with no arguments that decides
    whether the bell really has to be cached or not.

    For each file the "cachedFile(path)" signal will be emitted.
    When all files are done, "ready(Bell)" signal will be emitted.
    '''
    cachedFile = QtCore.pyqtSignal(str)
    ready = QtCore.pyqtSignal(Bell)

    @cls_logger
    def __init__(self, action, time):
        QtCore.QObject.__init__(self)
        self.log.info("Evvai porcoddio alle %s sonamo %s" % (time, action))
        self.action = action
        self.time = time
        self.checker = None

    def run(self):
        if self.checker is not None:
            if self.checker() is not True:
                self.log.info("Check falsed for action %s" % self.action)
                return
        self.log.debug("Caching %s" % self.action)

        #TODO: QtConcurrent.run
        cache_audio = []
        for path in self.action.get_audio(get_libraries()):
            cacher = cacheutils.CacheCopy(path)
            cacher.run()
            cache_audio.append(cacheutils.AudioCacheFile(cacher.path))
            self.cachedFile.emit(path)
        b = Bell(self.time, cache_audio)
        self.ready.emit(b)


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
