import os
import logging
logger = logging.getLogger(__name__)

from queue import Queue

from config_manager import get_config
from log import cls_logger
_bobina = None


class Bobina:
    """A Bobina manages the default random dir(s), with prefetching"""
    @cls_logger
    def __init__(self):
        self.log.debug("%s instantiating" % self.__class__.__name__)
        self.library = AudioLibrary(get_config().bobina_path)
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
        self.pool.put(el)
        self.prefetch(n-1)


class AudioLibrary:
    """Indexes some directories"""
    @cls_logger
    def __init__(self, dirs):
        self.log.debug("%s instantiating" % self.__class__.__name__)
        self.dirs = dirs
        self.file_list = []

        self.scan()

    def scan(self):
        #TODO: cache!
        for d in self.dirs:
            for root, subfolders, files in os.walk(d):
                for f in files:
                    if f.lower().endswith('.wav'):
                        self.file_list.append(os.path.join(root, f))
        self.file_list.sort()
