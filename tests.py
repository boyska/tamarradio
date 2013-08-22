import os
from datetime import timedelta

import avanti
import event


class DummyPlayer:
    '''what does a dummyplayer? Instead of playing audios, just records them'''
    def __init__(self):
        self.queue = []

    def enqueue(self, audio):
        self.queue.append(audio)

    def now_play(self, audio):
        print(audio)


class DummyAction:
    def __init__(self, name):
        self.audio = name


def dummyevent(name, time):
    alarm = event.Alarm(time)
    action = DummyAction(name)
    return event.Event(alarm, action)


def parse_filenext(fileobj):
    def header(f):
        #TODO: first next(f) must be parsed
        n = event.time_parse(next(f).strip())
        d = timedelta(seconds=int(next(f).strip()))
        return n, d

    def events(f):
        while True:
            line = next(f).strip()
            if line.startswith('---'):
                return
            ev_id, ev_time = line.split(':')
            yield dummyevent(ev_id, event.time_parse(ev_time))

    def result(f):
        return next(f).strip()
    now, duration = header(fileobj)
    ev = tuple(events(fileobj))
    res = result(fileobj)
    assert res in map(lambda e: e.name, ev) or res == 'BOBINA'
    return (now, duration, ev, res)


def test_files():
    for filename in filter(lambda n: n.endswith('.next.test'),
                           os.listdir('tests')):
        testcase = parse_filenext(iter(open(os.path.join('tests', filename))))
        yield next_event, testcase


def next_event(test):
    ev = avanti.next_event(test[0], test[1], test[2])
    if test[-1] == 'BOBINA':
        assert ev is None
    else:
        assert ev.name == test[-1]
