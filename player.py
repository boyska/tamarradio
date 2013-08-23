"""
An interface for basic play operation:
    play, pause, enqueue, manage playlist

The interface should _not_ reveal that it uses phonon, wrapping whatever is
needed and providing high-level methods and events
"""

import logging
logger = logging.getLogger(__name__)

from PyQt4.QtCore import QObject, pyqtSignal
from PyQt4.phonon import Phonon


#TODO: QtPlayer, qt main loop, etc
class QtPlayer(QObject):
    empty = pyqtSignal()

    def __init__(self):
        QObject.__init__(self)
        logger.debug("%s instantiating" % self.__class__.__name__)
        self.media = Phonon.MediaObject()
        Phonon.createPath(self.media, Phonon.AudioOutput(Phonon.MusicCategory,
                          self))
        self.media.finished.connect(self.empty)

    def enqueue(self, filename):
        src = Phonon.MediaSource(filename)
        logger.debug('accodo %s' % filename)
        self.media.enqueue(src)

    def now_play(self, audio):
        logger.debug("Now playing %s" % audio)
        self.media.setCurrentSource(Phonon.MediaSource(audio))
        self.media.play()
