'''
This module is just a collection of utilities to cache files easily
'''
import shutil
import os
import os.path
from tempfile import mkstemp

from config_manager import get_config


def safecopy(path):
    mkdir_p(get_config().CACHE_DIR)
    tmp = os.path.basename(path).encode('ascii', 'ignore')
    dest = os.path.join(get_config().CACHE_DIR, mkstemp(prefix=tmp))
    shutil.copy(path, dest)
    return dest


def mkdir_p(path):
    if os.path.exists(path) and os.path.isdir(path):
        return
    os.makedirs(path)
