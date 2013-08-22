import os
import logging
logger = logging.getLogger(__name__)

from queue import Queue
_bobina = None


class Bobina:
    """A Bobina manages the default random dir(s), with prefetching"""
    def __init__(self, dirs):
        self.library = AudioLibrary(dirs)
        self.pool = Queue()
        self.library_index = 0

        self.prefetch(10)

    def get_next(self):
        audio = self.pool.get_nowait()
        logger.debug("got %s from pool" % audio)
        self.prefetch()
        return audio

    def prefetch(self, n=1):
        """run a background process to get `n` new audio"""
        #TODO: make some sense out of it
        logger.debug("prefetching %d" % n)
        for i in range(n):
            #TODO: random.choice facile da usare, ma cosi' e' piu' testabile!
            try:
                el = self.library.file_list[self.library_index]
            except IndexError:
                self.library_index = 0
                el = self.library.file_list[self.library_index]
            self.library_index += 1
            logger.debug("fetching %s" % el)
            self.pool.put(el)


class AudioLibrary:
    """Indexes some directories"""
    def __init__(self, dirs):
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
