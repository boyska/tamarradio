from datetime import datetime, timedelta
from pprint import pprint

from .alarms import FrequencyAlarm, SingleAlarm

from nose.tools import timed, eq_
now = datetime.now()


def days(n):
    return timedelta(days=n)


def test_single_creations():
    return SingleAlarm(datetime.now())


def test_freq_creations():
    return FrequencyAlarm(now - timedelta(days=1), 3600, now)


@timed(.1)
def test_single_ring():
    dt = now + days(1)
    s = SingleAlarm(dt)
    eq_(s.next_ring(),  dt)
    eq_(s.next_ring(now),  dt)
    assert s.next_ring(dt) is None, "%s - %s" % (str(s.next_ring(dt)), str(dt))
    assert s.next_ring(now + days(2)) is None
    assert s.has_ring(dt)
    assert not s.has_ring(now)
    assert not s.has_ring(now + days(2))


@timed(.1)
def test_single_all():
    dt = now + timedelta(days=1)
    s = SingleAlarm(dt)
    eq_(list(s.all_rings()),  [dt])
    eq_(list(s.all_rings(now)),  [dt])
    eq_(list(s.all_rings(now + days(2))),  [])


@timed(0.2)
def test_freq_ring():
    f = FrequencyAlarm(now - days(1), 3600, now + days(1))
    print(now, "NOW")
    assert f.next_ring(now) is not None
    assert f.next_ring(now) != now
    assert now not in f.all_rings(now)
    allr = list(f.all_rings(now))
    eq_(len(allr), 24)

    eq_(len(tuple(f.all_rings(now + days(2)))), 0)

    allr = tuple(f.all_rings(now - days(20)))
    eq_(f.next_ring(now - days(20)), now - days(1))
    eq_(len(allr), 49, pprint(allr))
