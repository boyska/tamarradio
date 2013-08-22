import os
from datetime import datetime
import functools
import logging
logger = logging.getLogger(__name__)


def time_parse(s):
    return datetime.strptime(s, r'%Y-%m-%d-%H-%M-%S')


class EventLoader:
    def __init__(self, path):
        self.events = set()
        self.path = path
        self.events.update(self.rescan())

    def rescan(self):
        for d in self.path:
            for root, subfolders, files in os.walk(d):
                for f in files:
                    #the filename is the event date
                    #the content is the audio itself
                    #(event specification is yet to come)
                    if f.split('.')[-1].lower() in ('.wav', '.mp3', '.ogg'):
                        try:
                            base = f.split('.')[1]
                            date = time_parse(base)
                            ev = Event(Alarm(date), os.path.join(root, f))
                            if ev not in self.events:
                                yield ev
                        except Exception as exc:
                            logger.debug("Event %s skipped: %s" % (f, exc))
                            pass


@functools.total_ordering
class Event:
    def __init__(self, alarm, action):
        self.alarm = alarm
        self.action = action

    def __lt__(self, other):
        # a duck is crying for this "isinstance"
        # wait: it's not a duck, but it squaws like a duck...
        if(isinstance(other, datetime)):
            return self.alarm < other
        return self.alarm < other.alarm

    def __str__(self):
        return 'Event <%s, %s>' % (self.name, str(self.time))


@functools.total_ordering
class Alarm:
    def __init__(self, time):
        self.time = time

    def __lt__(self, other):
        # a duck is crying for this "isinstance"
        # wait: it's not a duck, but it squasw like a duck...
        if(isinstance(other, datetime)):
            return self.time < other
        return self.time < other.time

    def __str__(self):
        return 'Alarm <%s>' % (str(self.time))
