from nose.tools import eq_

from .actions import RandomFromPlaylistAction

class MockAudioLibrary:
    def __init__(self, iterable):
        self.file_list = list(iterable)


def setup_one():
    return {'one': MockAudioLibrary(range(5))}


def test_len():
    '''The number of track must be exactly as specified'''
    raccolte = setup_one()

    def check(raccolte, n, name):
        act = RandomFromPlaylistAction(n, name)
        audio = act.get_audio(raccolte)
        eq_(len(audio), n), "%s - %d (%d)" % (str(audio), n, len(audio))

    for i in range(6):
        yield check, raccolte, i, 'one'


def test_in():
    '''The elements must all be in the list'''
    raccolte = setup_one()

    def check(raccolte, n, name):
        act = RandomFromPlaylistAction(n, name)
        audio = act.get_audio(raccolte)
        for el in audio:
            assert el in raccolte[name].file_list
    for i in range(6):
        yield check, raccolte, i, 'one'


def test_nodups():
    '''There should be no duplicates'''
    raccolte = setup_one()

    def check(raccolte, n, name):
        act = RandomFromPlaylistAction(n, name)
        audio = act.get_audio(raccolte)
        eq_(len(audio), len(set(audio)))
    for i in range(6):
        yield check, raccolte, i, 'one'
