"""
This is Compagno Automagico, the main loop

DEPRECATED: see the controller.py to understand the new structure
"""

import sys
import logging
logger = logging.getLogger(__name__)
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

from PyQt4 import QtCore
from PyQt4.QtCore import SIGNAL

from bobina import get_bobina
from player import QtPlayer as Player


def loop_next():
    #TODO: check for event and add evt.get_audiotante()
    return get_bobina().get_next()


def main():
    logger.debug('inside the loop')
    #player.enqueue(loop_next())
    player.media.stop()
    player.media.clear()

    def on_finished(*args):
        logger.debug('finished!')
        assert player.media.state() == 1
        assert len(player.media.queue()) == 0
        n = loop_next()
        player.now_play(n)

    player.media.finished.connect(on_finished)
    player.now_play(loop_next())


class Tamarradio(QtCore.QCoreApplication):
    started = QtCore.pyqtSignal()

    def __init__(self, *args):
        QtCore.QCoreApplication.__init__(self, *args)
        self.setApplicationName('tamarradio')
        QtCore.QTimer.singleShot(0, self, SIGNAL('start_app()'))

if __name__ == '__main__':
    print("You are using compagno.py, which is DEPRECATED")
    logging.basicConfig(level=logging.DEBUG)
    logger.info('start')
    app = Tamarradio(sys.argv)
    app.connect(app, QtCore.SIGNAL('start_app()'), main)
    logger.debug('app-ed')
    player = Player()
    logger.debug('player-ed')
    ret = app.exec_()
    logger.info('end')
    sys.exit(ret)
