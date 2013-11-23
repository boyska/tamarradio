import os
import logging
logger = logging.getLogger(__name__)
from queue import Queue

from PyQt4 import QtCore

from config_manager import get_config
from log import cls_logger
from cacheutils import CacheCopy

_libraries = {}


def get_libraries():
    return _libraries


def find_libraries(path):
    path = os.path.abspath(path)
    for directory in next(os.walk(path))[1]:
        yield directory, AudioLibrary([os.path.join(path, directory)])


class Bobina:
    """A Bobina manages the default random dir(s), with prefetching"""
    @cls_logger
    def __init__(self):
        self.log.debug("%s instantiating" % self.__class__.__name__)
        self.library = AudioLibrary(get_config()['BOBINA_PATH'])
        self.pool = Queue()
        self.library_index = 0

        self.prefetch(10)

    def get_next(self):
        audio = self.pool.get_nowait()
        self.log.debug("got %s from pool" % audio)
        self.prefetch()
        return os.path.abspath(audio)

    def prefetch(self, n=1):
        """run a background process to get `n` new audio"""
        #TODO: make some sense out of it
        if n <= 0:
            return
        #TODO: random.choice facile da usare, ma cosi' e' piu' testabile!
        try:
            el = self.library.file_list[self.library_index]
        except IndexError:
            self.library_index = 0
            el = self.library.file_list[self.library_index]
        self.library_index = (self.library_index + 1) % \
            len(self.library.file_list)
        self.prepare(el)
        self.prefetch(n-1)

    def prepare(self, el):
        '''fetch an element and put into the queue'''
        self.log.debug("Preparing %s" % el)
        copy_process = CacheCopy(el)

        QtCore.QObject.connect(copy_process, QtCore.SIGNAL('copied(QString)'),
                               lambda path: self.pool.put(path),
                               QtCore.Qt.QueuedConnection)
        copy_process.start()


class AudioLibrary:
    """Indexes some directories"""
    @cls_logger
    def __init__(self, dirs):
        self.log.debug("%s instantiating(%s)" % (self.__class__.__name__, dirs))
        self.dirs = dirs
        #This implementation is highly inefficient, because it does not rely on
        #an external file, and consumes lot of memory
        self.file_list = []

        self.scan()

    def scan(self):
        #TODO: cache!
        for d in self.dirs:
            if not os.path.exists(d):
                self.log.warn("Directory %s does not exist, skipping" % d)
                continue
            for root, subfolders, files in os.walk(d):
                for f in files:
                    if f.lower().endswith('.wav'):
                        self.file_list.append(
                            os.path.abspath(os.path.join(root, f)))
        self.file_list.sort()
