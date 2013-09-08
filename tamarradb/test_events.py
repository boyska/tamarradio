from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from nose.tools import eq_, raises

from .alarms import *
from .actions import *
from .event import *

now = datetime.now()


# http://sontek.net/blog/detail/writing-tests-for-pyramid-and-sqlalchemy
class TestEvent:
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine('sqlite:///:memory:')
        cls.Session = sessionmaker()

    def setUp(self):
        connection = self.engine.connect()
        self.trans = connection.begin()
        self.Session.configure(bind=connection)
        self.session = self.Session(autocommit=False, autoflush=False,
                                    bind=self.engine)
        Event.session = self.session
        Base.metadata.create_all(self.engine)

    def tearDown(self):
        self.trans.rollback()
        self.session.close()
        Base.metadata.drop_all(self.engine)

    def test_empty(self):
        e = Event('test')
        self.session.add(e)
        assert e.action is None
        e.alarm

    def test_attach(self):
        e = Event('test')
        self.session.add(e)
        e.action = RandomFromPlaylistAction(2, 'asd')
        e.alarm = SingleAlarm(now)

    @raises
    def test_wrong_type(self):
        e = Event('test')
        e.alarm = RandomFromPlaylistAction(2, 'asd')
        e.action = SingleAlarm(now)

    def test_get_one(self):
        e = Event('test')
        self.session.add(e)
        self.session.commit()
        eq_(len(list(self.session.query(Event))), 1)

    def test_get_join(self):
        e = Event('test')
        self.session.add(e)
        e.action = RandomFromPlaylistAction(2, 'asd')
        e.alarm = SingleAlarm(now)
        self.session.commit()
        eq_(len(list(self.session.query(Event))), 1)
        eq_(len(list(self.session.query(Alarm))), 1)
        eq_(len(list(self.session.query(Action))), 1)
        got_e = self.session.query(Event).first()
        print(got_e.action.type)
        assert isinstance(got_e.action, Action)
        assert isinstance(got_e.action, RandomFromPlaylistAction)
        eq_(got_e.action.n, 2)
        eq_(got_e.action.playlist, 'asd')
        print(got_e.alarm)
        assert isinstance(got_e.alarm, Alarm)
        assert isinstance(got_e.alarm, SingleAlarm)
        eq_(got_e.alarm.dt, now)
