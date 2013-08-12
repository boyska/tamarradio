"""
An interface for basic play operation:
    play, pause, enqueue, manage playlist
"""

import logging
logger = logging.getLogger(__name__)

from PyQt4.QtCore import QObject
from PyQt4.phonon import Phonon


#TODO: QtPlayer, qt main loop, etc
class QtPlayer(QObject):
    def __init__(self):
        QObject.__init__(self)
        self.media = Phonon.MediaObject()
        Phonon.createPath(self.media, Phonon.AudioOutput(Phonon.MusicCategory,
                          self))

    def enqueue(self, filename):
        src = Phonon.MediaSource(filename)
        logger.debug('accodo %s' % filename)
        self.media.enqueue(src)
