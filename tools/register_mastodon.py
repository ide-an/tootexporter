from mastodon import Mastodon

Mastodon.create_app(
    'tootexporter',
    redirect_uris="http://127.0.0.1:5000/callback",
    api_base_url = 'https://gensokyo.cloud',
    to_file = 'client.secret'
)
