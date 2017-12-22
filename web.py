from flask import Flask,render_template,g,redirect,request,session,url_for,abort,flash
from mastodon import Mastodon
import db
from datetime import datetime
from pytz import timezone

app = Flask(__name__)

def get_mastodon(access_token=None):
    return Mastodon(
        client_id = 'client.secret',
        access_token = access_token,
        api_base_url = 'https://gensokyo.cloud'
    )

@app.teardown_appcontext
def close_db(error):
    db.close_db()

@app.route('/')
def index():
    user = None
    dbdata = None
    if 'user' in session:
        user = session['user']
        dbdata = db.get_user_by_mastodon_id(user['id'])
        snapshots = db.get_snapshots_by_owner(dbdata['id'])
    return render_template('hello.html', name='john', user=user, dbdata = dbdata, snapshots= snapshots)

@app.route('/snapshot', methods=['POST'])
def save_snapshot():
    if 'user' not in session:
        abort(401)
    user = db.get_user_by_mastodon_id(session['user']['id'])
    if not(validate_snapshot_form()):
        # TODO: show error message
        flash("なんか入力がミスってる")
        return redirect(url_for('index'))
    snap_type = request.form['snap_type']
    snap_start = jpdatetime(request.form['snap_start'])
    snap_end = jpdatetime(request.form['snap_end'])
    app.logger.debug("snapshot: type %s, start %s, end %s", snap_type, snap_start, snap_end)
    db.add_snapshot(user['id'], snap_type, snap_start, snap_end)
# TODO: enqueue
    return redirect(url_for('index'))

def validate_snapshot_form():
    try:
        snap_start = jpdatetime(request.form['snap_start'])
        snap_end = jpdatetime(request.form['snap_end'])
        snap_type = request.form['snap_type']
        if snap_type not in ["toot", "fav"]:
            return False
        return True
    except Exception as e:
        app.logger.debug(e)
        return False

def jpdatetime(datetime_str):
    return timezone("Asia/Tokyo").localize(datetime.strptime(datetime_str, "%Y-%m-%d"))

# OAuth
SESSION_ACCESS_TOKEN = 'access_token'
SESSION_USER = 'user'
@app.route('/login')
def login():
    mastodon = get_mastodon()
    return redirect(mastodon.auth_request_url(redirect_uris='http://127.0.0.1:5000/callback',scopes=['read']))

@app.route('/callback')
def callback():
    code = request.args.get('code','')
    mastodon = get_mastodon()
    access_token = mastodon.log_in(code=code,redirect_uri='http://127.0.0.1:5000/callback',scopes=['read'])
    user = mastodon.account_verify_credentials()
# create session
    session[SESSION_ACCESS_TOKEN] = access_token
    session[SESSION_USER] = user
# create user db
    db.add_or_create_user(access_token, user)
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop(SESSION_ACCESS_TOKEN, None)
    session.pop(SESSION_USER, None)
    return redirect(url_for('index'))

app.secret_key = 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
