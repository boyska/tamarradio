import random

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

__all__ = ['Action', 'RandomFromPlaylistAction']

Base = declarative_base()


class Action(Base):
    __tablename__ = 'action'
    id = Column(Integer, primary_key=True)

    def __init__(self, event):
        self.event_id = event.id

    def get_audio(self, controller):
        '''
        The action got "hydrated" with the controller. It's however _forbidden_
        for an action to act on the player.
        An Action should approach "read-only" to the controller, reading
        playlists and returning a list of audio files (that needs to be cached!)
        '''
        raise NotImplementedError()


class RandomFromPlaylistAction(Action):
    __tablename__ = 'action_random'
    id = Column(Integer, ForeignKey('action.id'), primary_key=True)
    n = Column(Integer)
    playlist = Column(String)

    def __init__(self, n, playlist):
        self.n = n
        self.playlist = playlist

    def get_audio(self, controller):
        pl = controller.raccolte[self.playlist].file_list
        return random.sample(pl, self.n)
