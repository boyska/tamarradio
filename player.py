"""
An interface for basic play operation:
    play, pause, enqueue, manage playlist

The interface should _not_ reveal that it uses phonon, wrapping whatever is
needed and providing high-level methods and events

Interface:
    * now_play('/path/to/file'): flushes playlist, set to input, play
    * enqueue('/path/to/file')
    * reset(): flushes playlist and stop
Optional:
    * get_now_playing() -> String with path
"""

import logging
logger = logging.getLogger(__name__)
from config_manager import get_config

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

    def get_now_playing(self):
        return self.media.currentSource().fileName()

    def reset(self):
        self.queue = []
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
        if self.queue:
            self.now_play(self.queue.pop(0))
        else:
            self.empty.emit()

    def enqueue(self, filename):
        self.queue.append(filename)

    def now_play_sequence(self, audioseq):
        first = audioseq[0]
        queue = audioseq[1:]

        self.log.debug("Now playing %s" % first)
        self.reset()
        self.media.setCurrentSource(Phonon.MediaSource(first))

        if queue:
            self.log.debug("enqueuing %s" % queue)
            for filename in queue:
                self.enqueue(filename)

        self.media.play()

        if not self.media.currentSource().fileName() == first:
            self.log.debug("should be playing %s but is not" % first)
            self._on_error()
        else:
            self.log.debug("Ok, correctly playing %s (%s)" %
                           (self.media.currentSource(), first))



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
