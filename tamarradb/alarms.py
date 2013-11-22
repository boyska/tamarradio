from datetime import datetime, timedelta

from sqlalchemy import Column, Integer, DateTime, ForeignKey, String
from sqlalchemy.ext.declarative import declarative_base

from .event import Alarm

__all__ = ['SingleAlarm', 'FrequencyAlarm']
Base = declarative_base()


class SingleAlarm(Alarm):
    '''
    rings a single time
    '''
    __tablename__ = 'alarm_single'
    id = Column(Integer, ForeignKey('alarm.id'), primary_key=True)
    dt = Column(DateTime)

    type = Column(String(50))
    __mapper_args__ = {'polymorphic_identity': 'single'}

    def __init__(self, dt):
        self.dt = dt

    def next_ring(self, current_time=None):
        '''if current_time is None, it is now()'''
        if current_time is None:
            current_time = datetime.now()
        if current_time >= self.dt:
            return None
        return self.dt

    def has_ring(self, current_time=None):
        if current_time is None:
            current_time = datetime.now()
        return current_time == self.dt

    def to_json(self):
        return {'id': self.id, 'dt': self.dt.isoformat()}


class FrequencyAlarm(Alarm):
    '''
    rings on {t | exists a k integer >= 0 s.t. t = start+k*t, start<t<end}
    '''
    __tablename__ = 'alarm_freq'
    id = Column(Integer, ForeignKey('alarm.id'), primary_key=True)
    start = Column(DateTime, nullable=False)
    interval = Column(Integer, nullable=False)  # seconds (cambia in Interval?)
    end = Column(DateTime)

    type = Column(String(50))
    __mapper_args__ = {'polymorphic_identity': 'freq'}

    def __init__(self, start, interval, end=None):
        self.start = start
        self.interval = interval
        self.end = end

    def next_ring(self, current_time=None):
        '''if current_time is None, it is now()'''
        if current_time is None:
            current_time = datetime.now()
        if self.end is not None and current_time > self.end:
            return None
        if current_time < self.start:
            return self.start
        if self.end is not None:
            assert self.start <= current_time <= self.end
        else:
            assert self.start <= current_time
        n_interval = (current_time - self.start).total_seconds() // self.interval
        ring = self.start + timedelta(seconds=self.interval * n_interval)
        if ring == current_time:
            ring += timedelta(seconds=self.interval)
        if self.end is not None and ring > self.end:
            return None
        return ring

    def has_ring(self, current_time=None):
        if current_time is None:
            current_time = datetime.now()
        if not self.start >= current_time >= self.end:
            return False

        n_interval = (current_time - self.start).total_seconds() // self.interval
        return self.start + timedelta(seconds=self.interval * n_interval) == current_time

    def to_json(self):
        return {'id': self.id, 'start': self.start, 'interval': self.interval,
                'end': self.end}
