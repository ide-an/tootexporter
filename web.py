from flask import Flask,render_template,g,redirect,request,session,url_for,abort,flash
import db
from datetime import datetime
from pytz import timezone
import exporter
import os

app = Flask(__name__)
app.secret_key = os.environ['SESSION_SECRET']

def get_db():
    _db = getattr(g, 'db', None)
    if _db is None:
        g.db = db.Db()
    return g.db

@app.teardown_appcontext
def close_db(error):
    get_db().close_db()

@app.route('/')
def index():
    user = None
    dbdata = None
    snapshots = None
    if 'user' in session:
        user = session['user']
        dbdata = get_db().get_user_by_mastodon_id(user['id'])
        if dbdata is not None:
            snapshots = get_db().get_snapshots_by_owner(dbdata['id'])
    return render_template('hello.html', name='john', user=user, dbdata = dbdata, snapshots= snapshots)

@app.route('/snapshot', methods=['POST'])
def save_snapshot():
    if 'user' not in session:
        abort(401)
    user = get_db().get_user_by_mastodon_id(session['user']['id'])
    if not(validate_snapshot_form()):
        flash("なんか入力がミスってる")
        return redirect(url_for('index'))
    snap_type = request.form['snap_type']
    app.logger.debug("snapshot: type %s", snap_type)
    exporter.reserve_snapshot(user['id'], snap_type)
    return redirect(url_for('index'))

def validate_snapshot_form():
    try:
        snap_type = request.form['snap_type']
        if snap_type not in [db.SNAPSHOT_TYPE_TOOT, db.SNAPSHOT_TYPE_FAV]:
            return False
        return True
    except Exception as e:
        app.logger.debug(e)
        return False

def jpdatetime(datetime_str):
    return timezone("Asia/Tokyo").localize(datetime.strptime(datetime_str, "%Y-%m-%d"))

@app.route('/snapshot/<int:snapshot_id>', methods=['GET'])
def download_snapshot(snapshot_id):
    # validation
    if 'user' not in session: # 誰っす
        abort(401)
    user = get_db().get_user_by_mastodon_id(session['user']['id'])
    snapshot = db.get_snapshot(snapshot_id)
    if snapshot is None: # ないっす
        abort(404)
    if snapshot['owner'] != user['id']: # あんたのじゃないっす
        abort(401)
    if snapshot['status'] != db.SNAPSHOT_STATUS_DONE: # まだっす
        abort(404)
    # ダウンロード用URL作成
    url = exporter.generate_download_url(snapshot['bucket'], snapshot['key'])
    return redirect(url)

# OAuth
CALLBACK_URL =  os.environ['OAUTH_CALLBACK_URL']
SESSION_ACCESS_TOKEN = 'access_token'
SESSION_USER = 'user'
@app.route('/login')
def login():
    mastodon = exporter.get_mastodon()
    return redirect(mastodon.auth_request_url(redirect_uris=CALLBACK_URL,scopes=['read']))

@app.route('/callback')
def callback():
    code = request.args.get('code','')
    mastodon = exporter.get_mastodon()
    access_token = mastodon.log_in(code=code,redirect_uri=CALLBACK_URL,scopes=['read'])
    user = mastodon.account_verify_credentials()
# create session
    session[SESSION_ACCESS_TOKEN] = access_token
    session[SESSION_USER] = user
# create user db
    get_db().add_or_create_user(access_token, user)
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop(SESSION_ACCESS_TOKEN, None)
    session.pop(SESSION_USER, None)
    return redirect(url_for('index'))

