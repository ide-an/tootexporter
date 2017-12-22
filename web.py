from flask import Flask,render_template,g,redirect,request,session,url_for
from mastodon import Mastodon
import db

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

@app.route("/")
def index():
    user = None
    if "user" in session:
        user = session["user"]
    return render_template('hello.html', name="john", user=user)

# OAuth
SESSION_ACCESS_TOKEN = "access_token"
SESSION_USER = "user"
@app.route("/login")
def login():
    mastodon = get_mastodon()
    return redirect(mastodon.auth_request_url(redirect_uris="http://127.0.0.1:5000/callback",scopes=["read"]))

@app.route("/callback")
def callback():
    code = request.args.get("code","")
    mastodon = get_mastodon()
    access_token = mastodon.log_in(code=code,redirect_uri="http://127.0.0.1:5000/callback",scopes=["read"])
    user = mastodon.account_verify_credentials()
# create session
    session[SESSION_ACCESS_TOKEN] = access_token
    session[SESSION_USER] = user
# create user db
    db.add_or_create_user(access_token, user)
    return redirect(url_for("index"))

@app.route("/logout")
def logout():
    session.pop(SESSION_ACCESS_TOKEN, None)
    session.pop(SESSION_USER, None)
    return redirect(url_for("index"))

app.secret_key = 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
