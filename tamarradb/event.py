from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

__all__ = ['Event', 'Action', 'Alarm', 'Base']

Base = declarative_base()


#TODO: created Column
class Event(Base):
    __tablename__ = 'event'
    id = Column(Integer, primary_key=True)
    description = Column(String)
    alarm_id = Column(Integer, ForeignKey('alarm.id'))
    alarm = relationship('Alarm', backref='event', uselist=False)
    action_id = Column(Integer, ForeignKey('action.id'))
    action = relationship('Action', backref='event', uselist=False)

    def __init__(self, description):
        self.description = description

    def to_json(self):
        d = {'id': self.id, 'description': self.description}
        if self.action:
            d['action'] = self.action
        if self.alarm:
            d['alarm'] = self.alarm
        return d


class Action(Base):
    __tablename__ = 'action'
    id = Column(Integer, primary_key=True)

    type = Column(String(50))
    __mapper_args__ = {
        'polymorphic_identity': 'action',
        'polymorphic_on': type
    }

    def __init__(self, event):
        self.event_id = event.id

    def get_audio(self, libraries):
        '''
        The action got "hydrated" with the controller. It's however _forbidden_
        for an action to act on the player.
        An Action should approach "read-only" to the controller, reading
        playlists and returning a list of audio files (that needs to be cached)
        '''
        raise NotImplementedError()


class Alarm(Base):
    __tablename__ = 'alarm'
    id = Column(Integer, primary_key=True)
    #TODO: aggiungere colonna "expired" per segnare gli scaduti (query piu' efficiente)

    type = Column(String(50))
    __mapper_args__ = {
        'polymorphic_identity': 'alarm',
        'polymorphic_on': type
    }

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


