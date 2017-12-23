from mastodon import Mastodon
import os

Mastodon.create_app(
    'tootexporter',
    redirect_uris = os.environ['OAUTH_CALLBACK_URL'],
    api_base_url = os.environ['MASTODON_API_BASE'],
    to_file = 'client.secret'
)
