'''
This module is just a collection of utilities to cache files easily
'''
import shutil
import os
import os.path
from tempfile import mkstemp

from PyQt4 import QtCore

from config_manager import get_config
from log import cls_logger, ColoredLogger


def safecopy(path):
    log = ColoredLogger('safecopy')
    os.makedirs(get_config()['CACHE_DIR'].encode('utf-8'), exist_ok=True)
    tmp = os.path.basename(path + '.').encode('ascii', 'ignore').decode('ascii')
    cachedir = get_config()['CACHE_DIR']
    fd, destname = mkstemp(prefix=tmp, suffix=os.path.splitext(path)[1],
                           dir=cachedir)
    shutil.copy(path, destname)
    log.debug("Copied %s in %s" % (path, destname))

    return destname


class CacheCopy(QtCore.QThread):
    @cls_logger
    def __init__(self, original):
        QtCore.QThread.__init__(self)
        self.original = original
        self.path = None

    def __del__(self):
        self.wait()

    def run(self):
        self.path = safecopy(self.original)
        self.emit(QtCore.SIGNAL('copied(QString)'), self.path)
        return


class AudioCacheFile(str):
    def __new__(cls, s):
        return super(AudioCacheFile, cls).__new__(cls, s)

    def __del__(self):
        if get_config()['CLEAN_CACHE']:
            os.unlink(self)
