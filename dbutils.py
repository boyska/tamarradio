from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import tamarradb


def init_engine(path):
    engine = create_engine(path)
    tamarradb.Base.metadata.create_all(engine)
    return engine


def list_events(engine):
    session = sessionmaker(bind=engine)()
    for event in session.query(tamarradb.Event):
        print('%d "%s"\t%s\t%s' % (event.id, event.description,
                                   event.alarm, event.action))


def add_frequency_playlist(engine, nsec, playlist):
    session = sessionmaker(bind=engine)()
    event = tamarradb.Event('Automatically created')
    event.alarm = tamarradb.FrequencyAlarm(datetime.now(), nsec)
    event.action = tamarradb.RandomFromPlaylistAction(1, playlist)
    session.add(event)
    session.commit()

if __name__ == '__main__':
    import sys
    dbpath = 'sqlite:///%s' % sys.argv[1]
    cmd = sys.argv[2]
    if cmd == 'list':
        list_events(init_engine(dbpath))
    elif cmd == 'add_frequency_playlist':
        nsec, filename = sys.argv[3:]
        add_frequency_playlist(init_engine(dbpath), int(nsec), filename)
    else:
        print('Error: command not valid', file=sys.stderr)
        sys.exit(1)
