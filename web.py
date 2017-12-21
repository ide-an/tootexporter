from flask import Flask,render_template,g,redirect,request,session,url_for
from mastodon import Mastodon

app = Flask(__name__)

def get_mastodon(access_token=None):
    return Mastodon(
        client_id = 'client.secret',
        access_token = access_token,
        api_base_url = 'https://gensokyo.cloud'
    )

@app.route("/")
def index():
    user = None
    if "user" in session:
        user = session["user"]
    return render_template('hello.html', name="john", user=user)

# OAuth
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
    session["access_token"] = access_token
    session["user"] = user
    return redirect(url_for("index"))

app.secret_key = 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
