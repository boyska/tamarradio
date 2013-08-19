import os
import sys

import nose


class Event:
    def __init__(self, name, time):
        self.name = name
        self.time = time


def parse_filenext(fileobj):
    def header(f):
        #TODO: first next(f) must be parsed
        n = next(f).strip()
        d = next(f).strip()
        return n,d

    def events(f):
        while True:
            line = next(f).strip()
            if line.startswith('---'):
                return
            ev_id, ev_time = line.split(':')
            yield Event(ev_id, ev_time)

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
        yield next_event,\
            parse_filenext(iter(open(os.path.join('tests', filename))))


def next_event(data):
    #TODO: test!
    for test in data:
        assert blah(*test[:-1]) == test[-1]
