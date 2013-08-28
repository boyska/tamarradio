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

from log import cls_logger


#TODO: QtPlayer, qt main loop, etc
class QtPlayer(QObject):
    empty = pyqtSignal()

    @cls_logger
    def __init__(self):
        QObject.__init__(self)
        logger.debug("%s instantiating" % self.__class__.__name__)
        self.media = Phonon.MediaObject()
        Phonon.createPath(self.media, Phonon.AudioOutput(Phonon.MusicCategory,
                          self))
        self.media.finished.connect(self._on_finished)

        assert self.media.state() == 1
        assert len(self.media.queue()) == 0
        self.media.stop()
        self.media.clear()

    def _on_finished(self):
        self.empty.emit()

    def enqueue(self, filename):
        src = Phonon.MediaSource(filename)
        self.log.debug('enqueue %s' % filename)
        self.media.enqueue(src)

    def now_play(self, audio):
        self.log.debug("Now playing %s" % audio)
        self.reset()
        src = Phonon.MediaSource(audio)
        self.media.setCurrentSource(src)
        self.media.play()
