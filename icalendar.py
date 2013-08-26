import sys


# import icalendar
# from icalendar import Calendar, Event

import vobject

class myical:
	def __init__(self, fname):
		self.fname = fname
		self.cal = vobject.readOne( open(self.fname, 'rb').read() )
		self.event = self.cal.vevent

	def lista(self):
		for ev in self.cal.vevent_list:
			print ev

	def trash(self):
		print "pretty print"
		cal.prettyPrint()

	def det(self):
		print "--------"
		print self.event.sortChildKeys()
		print "summary: ", self.event.getChildValue('summary')
		print "start:", str(self.event.getChildValue('dtstart'))
		# event.getChildValue('dtstart') is datetime.date() object
		print "end:", str(self.event.getChildValue('dtend'))


if __name__ == "__main__":
	m = myical(sys.argv[1])
	m.lista()
	m.det()


