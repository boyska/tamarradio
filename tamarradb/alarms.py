from datetime import datetime, timedelta

from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

__all__ = ['Alarm', 'SingleAlarm', 'FrequencyAlarm']
Base = declarative_base()


class Alarm(Base):
    __tablename__ = 'alarm'
    id = Column(Integer, primary_key=True)
    #TODO: aggiungere colonna "expired" per segnare gli scaduti (query piu' efficiente)

    def __init__(self, event):
        self.event_id = event.id

    def next_ring(self, current_time=None):
        '''if current_time is None, it is now(); returns the next time it will ring; or None if it will not anymore'''
        raise NotImplementedError()

    def has_ring(self, time=None):
        raise NotImplementedError()

    def all_rings(self, current_time=None):
        '''
        all future rings
        this, of course, is an iterator (they could be infinite)
        '''
        ring = self.next_ring(current_time)
        while ring is not None:
            yield ring
            ring = self.next_ring(ring)


class SingleAlarm(Alarm):
    '''
    rings a single time
    '''
    __tablename__ = 'alarm_single'
    id = Column(Integer, ForeignKey('alarm.id'), primary_key=True)
    dt = Column(DateTime)

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


class FrequencyAlarm(Alarm):
    '''
    rings on {t | exists a k integer >= 0 s.t. t = start+k*t, start<t<end}
    '''
    __tablename__ = 'alarm_freq'
    id = Column(Integer, ForeignKey('alarm.id'), primary_key=True)
    start = Column(DateTime, nullable=False)
    interval = Column(Integer, nullable=False)  # seconds (cambia in Interval?)
    end = Column(DateTime)

    def __init__(self, start, interval, end=None):
        self.start = start
        self.interval = interval
        self.end = end

    def next_ring(self, current_time=None):
        '''if current_time is None, it is now()'''
        if current_time is None:
            current_time = datetime.now()
        if current_time > self.end:
            return None
        if current_time < self.start:
            return self.start
        assert self.start <= current_time <= self.end
        n_interval = (current_time - self.start).total_seconds() // self.interval
        ring = self.start + timedelta(seconds=self.interval * n_interval)
        if ring == current_time:
            ring += timedelta(seconds=self.interval)
        if ring > self.end:
            return None
        return ring

    def has_ring(self, current_time=None):
        if current_time is None:
            current_time = datetime.now()
        if not self.start >= current_time >= self.end:
            return False

        n_interval = (current_time - self.start).total_seconds() // self.interval
        return self.start + timedelta(seconds=self.interval * n_interval) == current_time
