first line is format; by now, there's just one format; we'll call it "1"

    # format=1

then, comes the current time in YYYY-MM-DD-HH-MM-SS
third line is the length (in seconds) of tracks in "bobina", separated by a colon. When they're over, bobina will end.
To get a 2minutes, then a 3minutes, then a 30seconds track

    120;180;30

Then, comes a list of events, described as ID:datetime=length .

After that, a separator: line with three dashes

    ---

Then the result comes, with the ID of the next event to be executed. Between IDs,
BOBINA is a reserved word, to be used where no event matches (and bobina should just go on)

Example 1:

    # format=1
    2013-08-15-12-00-30
    180
    wron1:2013-08-15-12-00-50
    wron2:2013-08-15-12-01-50
    right:2013-08-15-12-02-50
    wron3:2013-08-15-12-03-31
    ---
    right

Example 2:

    # format=1
    2013-08-15-11-00-30
    180
    wron1:2013-08-15-12-00-50
    wron2:2013-08-15-12-01-50
    right:2013-08-15-12-02-50
    wron3:2013-08-15-12-03-31
    ---
    BOBINA

(all events are too far in time)
