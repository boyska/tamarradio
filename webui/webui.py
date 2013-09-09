import sys
import json
from datetime import datetime

from flask import Flask, Response, render_template, abort
from flask_bootstrap import Bootstrap
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.orm import joinedload

sys.path.append('..')
import tamarradb
app = Flask(__name__,
            template_folder='templates',
            static_folder='static',
            static_url_path='/static')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)
bootstrap = Bootstrap(app)
tamarradb.Base.metadata.create_all(db.engine)


def _json_default(self, obj):
    return getattr(obj.__class__, "to_json", _json_default.default)(obj)
_json_default.default = json.JSONEncoder().default  # save unmodified default
json.JSONEncoder.default = _json_default  # replacement


@app.route("/")
def home():
    return Response('Indirizzi validi: \n * %s' % '\n * '.join(
        sorted((r.rule for r in app.url_map.iter_rules()))),
        mimetype='text/plain')

#####
# API
#####

@app.route("/api/event/view/<event_id>")
def api_event_view(event_id):
    return Response(json.dumps(list(db.session.query(tamarradb.Event).
                    filter(tamarradb.Event.id == event_id))),
                    mimetype='application/json')


@app.route("/api/event/view")
def api_event_view_all():
    return Response(json.dumps(list(db.session.query(tamarradb.Event))),
                    mimetype='application/json')


#####
# TEST
#####

#TODO: remove me, I'm just an utility for quick test
@app.route("/test/add")
def event_add():
    e = tamarradb.Event('new')
    db.session.add(e)
    db.session.commit()
    e.action = tamarradb.RandomFromPlaylistAction(e.id + 1, 'foo%d' % e.id)
    e.alarm = tamarradb.SingleAlarm(datetime.now())
    db.session.commit()
    return str(e.id)

#####
# User Interface
#####


@app.route('/event/view')
def event_view_all():
    events = list(
        db.session.query(tamarradb.Event).
        options(joinedload('alarm'),
                joinedload('action')
                )
    )
    return render_template('view_all.html', events=events)


@app.route('/event/view/<event_id>')
def event_view(event_id):
    event = db.session.query(tamarradb.Event).filter(tamarradb.Event.id==event_id).first()
    if event is None:
        abort(404)
    return render_template('view.html', event=event)


@app.route("/event/edit/<id>")
def event_edit(event_id):
    event_id = int(event_id)

    return "welcome"

if __name__ == "__main__":
        app.run(debug=True)
