import random

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

from .event import Action
__all__ = ['RandomFromPlaylistAction']

Base = declarative_base()


class RandomFromPlaylistAction(Action):
    __tablename__ = 'action_random'
    id = Column(Integer, ForeignKey('action.id'), primary_key=True)
    n = Column(Integer)
    playlist = Column(String)

    type = Column(String(50))
    __mapper_args__ = {'polymorphic_identity': 'random_from_playlist'}

    def __init__(self, n, playlist):
        self.n = n
        self.playlist = playlist

    def get_audio(self, libraries):
        '''Returns a list of paths to audio files'''
        pl = libraries[self.playlist].file_list
        return random.sample(pl, self.n)

    def to_json(self):
        return {'id': self.id, 'n': self.n, 'playlist': self.playlist}

    def __str__(self):
        return 'RandomFromPlaylistAction(%d from %s)' % \
            (self.n, self.playlist)
