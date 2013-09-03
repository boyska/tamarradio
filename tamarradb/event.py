from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

from .alarms import Alarm

__all__ = ['Event']

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
