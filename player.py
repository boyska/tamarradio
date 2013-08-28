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
        self.log.debug("%s instantiating" % self.__class__.__name__)
        self.reset()
        # uberdebug
        self.media.stateChanged.connect(self._on_state_changed)
        self.media.currentSourceChanged.connect(self._on_source_changed)

        self.reset()

    def _on_state_changed(self, new, old):
        self.log.debug("STATE %d -> %d" % (old, new))

    def _on_source_changed(self, src):
        self.log.debug("SRC %s [%s]" % (str(src), src.fileName()))

    def reset(self):
        self.media = Phonon.MediaObject()
        self.media.finished.connect(self._on_finished)
        Phonon.createPath(self.media, Phonon.AudioOutput(Phonon.MusicCategory,
                          self))
        self.media.stop()
        self.media.clear()
        assert self.media.state() == 1
        assert len(self.media.queue()) == 0

    def _on_error(self):
        self.log.warning("Error playing! %s [%s]" %
                         (self.media.errorType(), self.media.errorString()))
        self._on_finished()

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

        if not self.media.currentSource().fileName() == audio:
            self.log.debug("should be playing %s but is not" % audio)
            self._on_error()
        else:
            self.log.debug("Ok, correctly playing %s (%s)" %
                           (self.media.currentSource(), audio))
