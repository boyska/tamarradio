from flask_wtf import Form
from wtforms import TextField, IntegerField, DateTimeField, SelectField,\
    FormField
from wtforms.validators import DataRequired


class SingleAlarmForm(Form):
    dt = DateTimeField('Datetime of play')


class FreqAlarmForm(Form):
    start = DateTimeField('Datetime of start')
    min = IntegerField('every X minutes')
    end = DateTimeField('Datetime of end')


class AlarmForm(Form):
    type = SelectField('Which type?', choices=[
        ('frequency', 'Frequency'), ('single', 'Single')])
    single = FormField(SingleAlarmForm, 'Single')
    freq = FormField(FreqAlarmForm, 'Frequency')


class RandomPlaylistForm(Form):
    n = IntegerField('How many songs')
    playlist = TextField('Which playlist')


class ActionForm(Form):
    type = SelectField('Which type?', choices=[
        ('randplaylist', 'Random from playlist')])
    randplaylist = FormField(RandomPlaylistForm, 'Random from playlist')


class EventForm(Form):
    description = TextField('Description', validators=[DataRequired()])
    al = FormField(AlarmForm, 'Alarm')
    act = FormField(ActionForm, 'Action')


def event_filters():
    def is_sub(f):
        return isinstance(f, FormField)

    return {'wtf_is_subform': is_sub}
