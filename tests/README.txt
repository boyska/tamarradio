"next" test
=============

This kind of tests is defined in '*.next.test' files. The format is:

first line is the current time in YYYY-MM-DD-HH-MM-SS
second line is the length (in seconds) of current track in "bobina"
Then, comes a list of events, described as NAME:datetime=length .

After that, a separator: line with three dashes

    ---

Then the result comes, with the NAME of the next event to be executed. Between
NAMEs,
BOBINA is a reserved word, to be used where no event matches (and bobina should just go on)
