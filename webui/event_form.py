from flask_wtf import Form
from wtforms import TextField, IntegerField, DateTimeField, SelectField,\
    FormField
from wtforms.validators import DataRequired, Optional, any_of

# TODO: OnlyIfSelected dovrebbe far si che la validazione avvenga solo se il
# form e' selezionato nella select del form padre
OnlyIfSelected = Optional


class SingleAlarmForm(Form):
    dt = DateTimeField('Datetime of play', validators=[OnlyIfSelected()])


class FreqAlarmForm(Form):
    start = DateTimeField('Datetime of start', validators=[OnlyIfSelected()])
    min = IntegerField('every X minutes', validators=[OnlyIfSelected()])
    end = DateTimeField('Datetime of end', validators=[OnlyIfSelected()])


class AlarmForm(Form):
    type = SelectField('Which type?', choices=[
        ('none', ''), ('frequency', 'Frequency'), ('single', 'Single')],
        validators=[any_of(('frequency', 'single'))])
    single = FormField(SingleAlarmForm, 'Single')
    freq = FormField(FreqAlarmForm, 'Frequency')


class RandomPlaylistForm(Form):
    n = IntegerField('How many songs', validators=[OnlyIfSelected()])
    playlist = TextField('Which playlist', validators=[OnlyIfSelected()])


class ActionForm(Form):
    type = SelectField('Which type?', choices=[
        ('none', ''), ('randplaylist', 'Random from playlist')],
        validators=[any_of(('randplaylist',))])
    randplaylist = FormField(RandomPlaylistForm, 'Random from playlist')


class EventForm(Form):
    description = TextField('Description', validators=[DataRequired()])
    al = FormField(AlarmForm, 'Alarm')
    act = FormField(ActionForm, 'Action')


def event_filters():
    def is_sub(f):
        return isinstance(f, FormField)

    return {'wtf_is_subform': is_sub}
