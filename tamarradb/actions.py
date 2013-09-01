from sqlalchemy import Column, Integer
from sqlalchemy.ext.declarative import declarative_base
__all__ = ['Action']

Base = declarative_base()


class Action(Base):
    __tablename__ = 'action'
    id = Column(Integer, primary_key=True)

    def __init__(self, event):
        self.event_id = event.id
